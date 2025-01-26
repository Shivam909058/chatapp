from supabase_client import supabase
from security import hash_password, verify_password
from datetime import datetime, timedelta

class Database:
    @staticmethod
    def save_message(room_id: str, sender_id: str, sender_name: str, message: str):
        try:
            result = supabase.table('messages').insert({
                "room_id": room_id,
                "sender_id": sender_id,
                "sender_name": sender_name,
                "message": message
            }).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error saving message: {str(e)}")
            return None

    @staticmethod
    def get_messages(room_id: str, limit: int = 50):
        try:
            result = supabase.table('messages')\
                .select("*")\
                .eq('room_id', room_id)\
                .order('created_at', desc=False)\
                .limit(limit)\
                .execute()
            return result
        except Exception as e:
            print(f"Error getting messages: {str(e)}")
            return None

    @staticmethod
    def save_user(user_id: str, name: str, room_id: str):
        try:
            result = supabase.table('users').insert({
                "id": user_id,
                "name": name,
                "room_id": room_id
            }).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error saving user: {str(e)}")
            return None

    @staticmethod
    def delete_user(user_id: str):
        try:
            result = supabase.table('users')\
                .delete()\
                .eq('id', user_id)\
                .execute()
            return result
        except Exception as e:
            print(f"Error deleting user: {str(e)}")
            return None

    @staticmethod
    def get_room_users(room_id: str):
        try:
            result = supabase.table('users')\
                .select("*")\
                .eq('room_id', room_id)\
                .execute()
            return result.data
        except Exception as e:
            print(f"Error getting room users: {str(e)}")
            return []

    @staticmethod
    def create_room(room_id: str, password: str, created_by: str):
        try:
            # Hash the password before storing
            hashed_password = hash_password(password)
            result = supabase.table('rooms').insert({
                "room_id": room_id,
                "password": hashed_password,
                "created_by": created_by,
                "created_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat()
            }).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error creating room: {str(e)}")
            return None

    @staticmethod
    def verify_room_access(room_id: str, password: str) -> bool:
        try:
            result = supabase.table('rooms')\
                .select("*")\
                .eq('room_id', room_id)\
                .execute()
            
            if not result.data:
                return False
                
            room = result.data[0]
            
            # Verify the password
            if not verify_password(password, room['password']):
                return False
                
            # Update last activity
            supabase.table('rooms')\
                .update({"last_activity": datetime.now().isoformat()})\
                .eq('room_id', room_id)\
                .execute()
                
            return True
        except Exception as e:
            print(f"Error verifying room: {str(e)}")
            return False

    @staticmethod
    def cleanup_inactive_rooms(max_inactive_hours: int = 24):
        """Delete rooms that have been inactive for the specified duration"""
        try:
            cutoff_time = (datetime.now() - timedelta(hours=max_inactive_hours)).isoformat()
            supabase.table('rooms')\
                .delete()\
                .lt('last_activity', cutoff_time)\
                .execute()
        except Exception as e:
            print(f"Error cleaning up rooms: {str(e)}") 