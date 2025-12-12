#!/usr/bin/env python3
"""
ACWR Migration WebSocket Handler
Provides real-time progress updates via WebSocket connections
"""

import logging
import json
import asyncio
import websockets
from datetime import datetime
from typing import Dict, Set, Optional, Any
from flask import Blueprint, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import threading
import time

from acwr_migration_progress_tracker import (
    ACWRMigrationProgressTracker, ProgressEvent, ProgressEventType
)

logger = logging.getLogger(__name__)

# Create blueprint for migration WebSocket routes
acwr_migration_websocket = Blueprint('acwr_migration_websocket', __name__)

# Global progress tracker instance
progress_tracker = ACWRMigrationProgressTracker()

# WebSocket connections tracking
active_connections: Dict[str, Set[str]] = {}  # migration_id -> set of connection_ids
connection_migrations: Dict[str, str] = {}  # connection_id -> migration_id

class MigrationWebSocketHandler:
    """WebSocket handler for migration progress updates"""
    
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.logger = logging.getLogger(__name__)
        self.progress_tracker = progress_tracker
        
        # Subscribe to progress events
        self.subscriber_id = f"websocket_handler_{int(time.time())}"
        self.progress_tracker.subscribe(self.subscriber_id, self._handle_progress_event)
        
        # Setup SocketIO event handlers
        self._setup_socketio_handlers()
    
    def _setup_socketio_handlers(self):
        """Setup SocketIO event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            self.logger.info(f"Client connected: {request.sid}")
            emit('connected', {'message': 'Connected to migration progress updates'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            self.logger.info(f"Client disconnected: {request.sid}")
            self._remove_connection(request.sid)
        
        @self.socketio.on('subscribe_migration')
        def handle_subscribe_migration(data):
            """Handle migration subscription"""
            try:
                migration_id = data.get('migration_id')
                if not migration_id:
                    emit('error', {'message': 'Migration ID is required'})
                    return
                
                # Add connection to migration room
                join_room(migration_id)
                connection_migrations[request.sid] = migration_id
                
                if migration_id not in active_connections:
                    active_connections[migration_id] = set()
                active_connections[migration_id].add(request.sid)
                
                # Send current progress if available
                snapshot = self.progress_tracker.get_migration_progress(migration_id)
                if snapshot:
                    emit('progress_update', {
                        'migration_id': migration_id,
                        'snapshot': self._snapshot_to_dict(snapshot)
                    })
                
                self.logger.info(f"Client {request.sid} subscribed to migration {migration_id}")
                emit('subscribed', {
                    'migration_id': migration_id,
                    'message': f'Subscribed to migration {migration_id}'
                })
                
            except Exception as e:
                self.logger.error(f"Error handling migration subscription: {str(e)}")
                emit('error', {'message': f'Subscription failed: {str(e)}'})
        
        @self.socketio.on('unsubscribe_migration')
        def handle_unsubscribe_migration(data):
            """Handle migration unsubscription"""
            try:
                migration_id = data.get('migration_id')
                if migration_id:
                    leave_room(migration_id)
                    self._remove_connection_from_migration(request.sid, migration_id)
                else:
                    # Unsubscribe from all migrations
                    self._remove_connection(request.sid)
                
                emit('unsubscribed', {
                    'migration_id': migration_id,
                    'message': 'Unsubscribed from migration updates'
                })
                
            except Exception as e:
                self.logger.error(f"Error handling migration unsubscription: {str(e)}")
                emit('error', {'message': f'Unsubscription failed: {str(e)}'})
        
        @self.socketio.on('get_migration_progress')
        def handle_get_migration_progress(data):
            """Handle request for current migration progress"""
            try:
                migration_id = data.get('migration_id')
                if not migration_id:
                    emit('error', {'message': 'Migration ID is required'})
                    return
                
                snapshot = self.progress_tracker.get_migration_progress(migration_id)
                if snapshot:
                    emit('migration_progress', {
                        'migration_id': migration_id,
                        'snapshot': self._snapshot_to_dict(snapshot)
                    })
                else:
                    emit('error', {'message': f'No progress found for migration {migration_id}'})
                    
            except Exception as e:
                self.logger.error(f"Error getting migration progress: {str(e)}")
                emit('error', {'message': f'Failed to get progress: {str(e)}'})
        
        @self.socketio.on('get_migration_events')
        def handle_get_migration_events(data):
            """Handle request for migration events"""
            try:
                migration_id = data.get('migration_id')
                limit = data.get('limit', 100)
                
                if not migration_id:
                    emit('error', {'message': 'Migration ID is required'})
                    return
                
                events = self.progress_tracker.get_migration_events(migration_id, limit)
                emit('migration_events', {
                    'migration_id': migration_id,
                    'events': [self._event_to_dict(event) for event in events]
                })
                
            except Exception as e:
                self.logger.error(f"Error getting migration events: {str(e)}")
                emit('error', {'message': f'Failed to get events: {str(e)}'})
        
        @self.socketio.on('get_all_migrations')
        def handle_get_all_migrations():
            """Handle request for all active migrations"""
            try:
                snapshots = self.progress_tracker.get_all_migration_progress()
                emit('all_migrations', {
                    'migrations': [self._snapshot_to_dict(snapshot) for snapshot in snapshots]
                })
                
            except Exception as e:
                self.logger.error(f"Error getting all migrations: {str(e)}")
                emit('error', {'message': f'Failed to get migrations: {str(e)}'})
    
    def _handle_progress_event(self, event: ProgressEvent):
        """Handle progress events from the tracker"""
        try:
            migration_id = event.migration_id
            
            # Send to all subscribers of this migration
            if migration_id in active_connections:
                event_data = {
                    'event_type': event.event_type.value,
                    'migration_id': migration_id,
                    'user_id': event.user_id,
                    'timestamp': event.timestamp.isoformat(),
                    'data': event.data,
                    'message': event.message
                }
                
                # Emit to room (all subscribers of this migration)
                self.socketio.emit('progress_event', event_data, room=migration_id)
                
                # If it's a progress update, also send the current snapshot
                if event.event_type == ProgressEventType.PROGRESS_UPDATE:
                    snapshot = self.progress_tracker.get_migration_progress(migration_id)
                    if snapshot:
                        self.socketio.emit('progress_update', {
                            'migration_id': migration_id,
                            'snapshot': self._snapshot_to_dict(snapshot)
                        }, room=migration_id)
            
        except Exception as e:
            self.logger.error(f"Error handling progress event: {str(e)}")
    
    def _remove_connection(self, connection_id: str):
        """Remove connection from all migrations"""
        if connection_id in connection_migrations:
            migration_id = connection_migrations[connection_id]
            self._remove_connection_from_migration(connection_id, migration_id)
            del connection_migrations[connection_id]
    
    def _remove_connection_from_migration(self, connection_id: str, migration_id: str):
        """Remove connection from specific migration"""
        if migration_id in active_connections:
            active_connections[migration_id].discard(connection_id)
            if not active_connections[migration_id]:
                del active_connections[migration_id]
    
    def _snapshot_to_dict(self, snapshot) -> Dict[str, Any]:
        """Convert progress snapshot to dictionary"""
        return {
            'migration_id': snapshot.migration_id,
            'user_id': snapshot.user_id,
            'status': snapshot.status,
            'current_batch': snapshot.current_batch,
            'total_batches': snapshot.total_batches,
            'processed_activities': snapshot.processed_activities,
            'total_activities': snapshot.total_activities,
            'successful_calculations': snapshot.successful_calculations,
            'failed_calculations': snapshot.failed_calculations,
            'progress_percentage': round(snapshot.progress_percentage, 2),
            'estimated_completion': snapshot.estimated_completion.isoformat() if snapshot.estimated_completion else None,
            'processing_rate': round(snapshot.processing_rate, 2),
            'elapsed_time': round(snapshot.elapsed_time, 2),
            'last_update': snapshot.last_update.isoformat()
        }
    
    def _event_to_dict(self, event: ProgressEvent) -> Dict[str, Any]:
        """Convert progress event to dictionary"""
        return {
            'event_type': event.event_type.value,
            'migration_id': event.migration_id,
            'user_id': event.user_id,
            'timestamp': event.timestamp.isoformat(),
            'data': event.data,
            'message': event.message
        }
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics"""
        return {
            'total_connections': len(connection_migrations),
            'active_migrations': len(active_connections),
            'connections_per_migration': {
                migration_id: len(connections)
                for migration_id, connections in active_connections.items()
            }
        }

# REST API endpoints for migration progress
@acwr_migration_websocket.route('/api/migration/progress/<migration_id>', methods=['GET'])
def get_migration_progress_api(migration_id: str):
    """Get migration progress via REST API"""
    try:
        snapshot = progress_tracker.get_migration_progress(migration_id)
        if snapshot:
            return jsonify({
                'success': True,
                'migration_id': migration_id,
                'progress': {
                    'status': snapshot.status,
                    'current_batch': snapshot.current_batch,
                    'total_batches': snapshot.total_batches,
                    'processed_activities': snapshot.processed_activities,
                    'total_activities': snapshot.total_activities,
                    'successful_calculations': snapshot.successful_calculations,
                    'failed_calculations': snapshot.failed_calculations,
                    'progress_percentage': round(snapshot.progress_percentage, 2),
                    'estimated_completion': snapshot.estimated_completion.isoformat() if snapshot.estimated_completion else None,
                    'processing_rate': round(snapshot.processing_rate, 2),
                    'elapsed_time': round(snapshot.elapsed_time, 2),
                    'last_update': snapshot.last_update.isoformat()
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': f'No progress found for migration {migration_id}'
            }), 404
            
    except Exception as e:
        logger.error(f"Error getting migration progress: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@acwr_migration_websocket.route('/api/migration/events/<migration_id>', methods=['GET'])
def get_migration_events_api(migration_id: str):
    """Get migration events via REST API"""
    try:
        limit = request.args.get('limit', 100, type=int)
        events = progress_tracker.get_migration_events(migration_id, limit)
        
        return jsonify({
            'success': True,
            'migration_id': migration_id,
            'events': [
                {
                    'event_type': event.event_type.value,
                    'timestamp': event.timestamp.isoformat(),
                    'data': event.data,
                    'message': event.message
                }
                for event in events
            ]
        })
        
    except Exception as e:
        logger.error(f"Error getting migration events: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@acwr_migration_websocket.route('/api/migration/all', methods=['GET'])
def get_all_migrations_api():
    """Get all active migrations via REST API"""
    try:
        snapshots = progress_tracker.get_all_migration_progress()
        
        return jsonify({
            'success': True,
            'migrations': [
                {
                    'migration_id': snapshot.migration_id,
                    'user_id': snapshot.user_id,
                    'status': snapshot.status,
                    'progress_percentage': round(snapshot.progress_percentage, 2),
                    'processed_activities': snapshot.processed_activities,
                    'total_activities': snapshot.total_activities,
                    'last_update': snapshot.last_update.isoformat()
                }
                for snapshot in snapshots
            ]
        })
        
    except Exception as e:
        logger.error(f"Error getting all migrations: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@acwr_migration_websocket.route('/api/migration/stats', methods=['GET'])
def get_migration_stats_api():
    """Get migration statistics via REST API"""
    try:
        performance_metrics = progress_tracker.get_performance_metrics()
        subscriber_stats = progress_tracker.get_subscriber_stats()
        
        return jsonify({
            'success': True,
            'performance_metrics': performance_metrics,
            'subscriber_stats': subscriber_stats,
            'websocket_stats': {
                'total_connections': len(connection_migrations),
                'active_migrations': len(active_connections)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting migration stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def initialize_migration_websocket(socketio: SocketIO):
    """Initialize the migration WebSocket handler"""
    return MigrationWebSocketHandler(socketio)

