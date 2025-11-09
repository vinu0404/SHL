"""
Progress tracker component for showing processing progress in Chainlit
"""

import chainlit as cl
from typing import Optional


class ProgressTracker:
    """Component for tracking and displaying processing progress"""
    
    def __init__(self):
        self.active_trackers = {}
    
    async def create_tracker(self, message: str = "Processing...") -> str:
        """
        Create a new progress tracker
        
        Args:
            message: Initial message
            
        Returns:
            Tracker ID
        """
        # Create a message to act as progress tracker
        tracker_msg = cl.Message(content=f"⏳ {message}")
        await tracker_msg.send()
        
        tracker_id = tracker_msg.id
        self.active_trackers[tracker_id] = tracker_msg
        
        return tracker_id
    
    async def update(self, tracker_id: str, message: str, percentage: Optional[int] = None):
        """
        Update progress tracker
        
        Args:
            tracker_id: Tracker identifier
            message: Progress message
            percentage: Optional percentage (0-100)
        """
        if tracker_id not in self.active_trackers:
            return
        
        tracker_msg = self.active_trackers[tracker_id]
        
        # Build progress message
        if percentage is not None:
            # Create progress bar
            filled = int(percentage / 5)  # 20 blocks for 100%
            bar = "█" * filled + "░" * (20 - filled)
            content = f"⏳ {message}\n\n`{bar}` {percentage}%"
        else:
            content = f"⏳ {message}"
        
        # Update the message
        tracker_msg.content = content
        await tracker_msg.update()
    
    async def complete(self, tracker_id: str, message: str = "Complete!"):
        """
        Mark tracker as complete
        
        Args:
            tracker_id: Tracker identifier
            message: Completion message
        """
        if tracker_id not in self.active_trackers:
            return
        
        tracker_msg = self.active_trackers[tracker_id]
        
        # Update with completion message
        tracker_msg.content = f"✅ {message}"
        await tracker_msg.update()
    
    async def error(self, tracker_id: str, message: str = "Error occurred"):
        """
        Mark tracker as error
        
        Args:
            tracker_id: Tracker identifier
            message: Error message
        """
        if tracker_id not in self.active_trackers:
            return
        
        tracker_msg = self.active_trackers[tracker_id]
        
        # Update with error message
        tracker_msg.content = f"❌ {message}"
        await tracker_msg.update()
    
    async def remove(self, tracker_id: str):
        """
        Remove progress tracker
        
        Args:
            tracker_id: Tracker identifier
        """
        if tracker_id not in self.active_trackers:
            return
        
        tracker_msg = self.active_trackers[tracker_id]
        
        try:
            await tracker_msg.remove()
        except:
            pass  # Message might already be removed
        
        # Clean up
        del self.active_trackers[tracker_id]