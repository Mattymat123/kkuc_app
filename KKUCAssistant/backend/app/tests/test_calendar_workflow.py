"""
Test script for Calendar Booking Workflow
Demonstrates the three-step LangGraph workflow
"""
from app.workflows.calendar_workflow import CalendarWorkflow


def main():
    """Run the calendar booking workflow test"""
    print("\n" + "="*60)
    print("🧪 Testing Calendar Booking Workflow")
    print("="*60)
    
    # Initialize workflow
    workflow = CalendarWorkflow()
    
    # Run the workflow
    result = workflow.run()
    
    # Display results
    print("\n" + "="*60)
    print("📊 WORKFLOW RESULTS")
    print("="*60)
    
    if result["success"]:
        print("\n✅ Workflow completed successfully!")
        print(f"\n📅 Available slots found: {len(result['available_slots'])}")
        
        if result['available_slots']:
            print("\nAvailable time slots:")
            for slot in result['available_slots']:
                print(f"  • {slot['day']}, {slot['date']} at {slot['time']}")
        
        print(f"\n🎯 Selected slot: {result['selected_slot']['day']}, {result['selected_slot']['date']} at {result['selected_slot']['time']}")
        
        booking = result['booking']
        print(f"\n✅ Booking Status: {booking['status']}")
        print(f"   Name: {booking['name']}")
        print(f"   Date: {booking['date']}")
        print(f"   Time: {booking['time']}")
        print(f"   Event ID: {booking['event_id']}")
        print(f"   Verified: {booking['verified']}")
        if booking.get('link'):
            print(f"   Link: {booking['link']}")
        
    else:
        print(f"\n❌ Workflow failed: {result['error']}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
