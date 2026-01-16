"""
RabbitMQ Service for message queue operations
"""
import pika
import json
from typing import Dict, Any, Callable
from app.config import settings
import time

class RabbitMQService:
    """Service for RabbitMQ message queue operations"""
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self.host = settings.rabbitmq_host
        self.port = settings.rabbitmq_port
        self.user = settings.rabbitmq_user
        self.password = settings.rabbitmq_pass
    
    def connect(self):
        """Establish connection to RabbitMQ"""
        credentials = pika.PlainCredentials(self.user, self.password)
        parameters = pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )
        
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                
                # Declare queues
                self.channel.queue_declare(queue='design_tasks', durable=True)
                self.channel.queue_declare(queue='simulation_tasks', durable=True)
                self.channel.queue_declare(queue='vendor_tasks', durable=True)
                
                print(f"Connected to RabbitMQ at {self.host}:{self.port}")
                return True
                
            except Exception as e:
                retry_count += 1
                print(f"Failed to connect to RabbitMQ (attempt {retry_count}/{max_retries}): {e}")
                if retry_count < max_retries:
                    time.sleep(5)
                else:
                    print("Max retries reached. Could not connect to RabbitMQ.")
                    return False
    
    def publish_message(self, queue: str, message: Dict[str, Any]):
        """Publish a message to a queue"""
        if not self.channel:
            if not self.connect():
                raise Exception("Cannot publish message - not connected to RabbitMQ")
        
        try:
            self.channel.basic_publish(
                exchange='',
                routing_key=queue,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                )
            )
            print(f"Published message to queue '{queue}': {message.get('task_id', 'unknown')}")
        except Exception as e:
            print(f"Error publishing message: {e}")
            # Try to reconnect
            self.connect()
            raise
    
    def consume_messages(self, queue: str, callback: Callable):
        """Consume messages from a queue"""
        if not self.channel:
            if not self.connect():
                raise Exception("Cannot consume messages - not connected to RabbitMQ")
        
        def message_callback(ch, method, properties, body):
            try:
                message = json.loads(body)
                callback(message)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                print(f"Error processing message: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue=queue, on_message_callback=message_callback)
        
        print(f"Started consuming messages from queue '{queue}'")
        self.channel.start_consuming()
    
    def close(self):
        """Close connection to RabbitMQ"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            print("Closed RabbitMQ connection")

rabbitmq_service = RabbitMQService()
