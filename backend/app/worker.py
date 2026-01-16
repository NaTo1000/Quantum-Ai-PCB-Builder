"""
RabbitMQ Worker for processing background tasks
"""
import asyncio
from app.services.rabbitmq_service import rabbitmq_service
from app.services.design_service import design_service
from app.services.simulation_service import simulation_service

def process_design_task(message):
    """Process design generation task"""
    design_id = message.get("design_id")
    print(f"Processing design task: {design_id}")
    
    try:
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(design_service.process_design(design_id))
        loop.close()
        
        print(f"Design {design_id} processed successfully")
    except Exception as e:
        print(f"Error processing design {design_id}: {e}")

def process_simulation_task(message):
    """Process simulation task"""
    design_id = message.get("design_id")
    simulation_type = message.get("simulation_type", "full")
    print(f"Processing simulation task for design: {design_id}")
    
    try:
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            simulation_service.run_simulation(design_id, simulation_type)
        )
        loop.close()
        
        print(f"Simulation for design {design_id} completed successfully")
    except Exception as e:
        print(f"Error processing simulation for design {design_id}: {e}")

def main():
    """Main worker process"""
    print("Starting RabbitMQ worker...")
    
    # Connect to RabbitMQ
    if not rabbitmq_service.connect():
        print("Failed to connect to RabbitMQ. Exiting...")
        return
    
    print("Worker started and waiting for tasks...")
    
    try:
        # Start consuming from design queue
        rabbitmq_service.consume_messages('design_tasks', process_design_task)
    except KeyboardInterrupt:
        print("\nShutting down worker...")
        rabbitmq_service.close()
    except Exception as e:
        print(f"Worker error: {e}")
        rabbitmq_service.close()

if __name__ == "__main__":
    main()
