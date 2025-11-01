"""
Database Index Migration Script
Applies composite indexes for optimal query performance
"""

from sqlalchemy import create_engine, text
import models

def apply_indexes():
    """Apply composite indexes to improve query performance"""
    
    engine = models.engine
    
    indexes = [
        # Conversation indexes
        ("CREATE INDEX IF NOT EXISTS idx_chatbot_session ON conversations (chatbot_id, session_id);", 
         "Composite index for chatbot_id + session_id (unique customer queries)"),
        
        ("CREATE INDEX IF NOT EXISTS idx_chatbot_created ON conversations (chatbot_id, created_at);",
         "Composite index for chatbot_id + created_at (time-based queries)"),
        
        ("CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations (created_at);",
         "Index on created_at for conversations"),
        
        # Message indexes
        ("CREATE INDEX IF NOT EXISTS idx_conversation_created ON messages (conversation_id, created_at);",
         "Composite index for conversation_id + created_at"),
        
        ("CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages (created_at);",
         "Index on created_at for messages"),
        
        # Support ticket indexes
        ("CREATE INDEX IF NOT EXISTS idx_chatbot_status ON support_tickets (chatbot_id, status);",
         "Composite index for chatbot_id + status (ticket filtering)"),
        
        ("CREATE INDEX IF NOT EXISTS idx_chatbot_assigned ON support_tickets (chatbot_id, assigned_to);",
         "Composite index for chatbot_id + assigned_to (ticket assignment)"),
        
        ("CREATE INDEX IF NOT EXISTS idx_tickets_status ON support_tickets (status);",
         "Index on status for support tickets"),
        
        ("CREATE INDEX IF NOT EXISTS idx_tickets_assigned_to ON support_tickets (assigned_to);",
         "Index on assigned_to for support tickets"),
        
        ("CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON support_tickets (created_at);",
         "Index on created_at for support tickets"),
        
        # Subscription indexes
        ("CREATE INDEX IF NOT EXISTS idx_user_status ON subscriptions (user_id, status);",
         "Composite index for user_id + status (subscription queries)"),
        
        ("CREATE INDEX IF NOT EXISTS idx_subscriptions_plan_tier ON subscriptions (plan_tier);",
         "Index on plan_tier for subscriptions"),
        
        ("CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions (status);",
         "Index on status for subscriptions"),
    ]
    
    print("🔧 Applying database indexes for optimal performance...\n")
    
    with engine.connect() as conn:
        for sql, description in indexes:
            try:
                print(f"✓ {description}")
                conn.execute(text(sql))
                conn.commit()
            except Exception as e:
                print(f"⚠ Warning: {description} - {str(e)}")
    
    print("\n✅ Index migration completed!")
    print("\n📊 Analyzing indexes...")
    
    # Analyze tables for better query planning
    tables = ['conversations', 'messages', 'support_tickets', 'subscriptions']
    with engine.connect() as conn:
        for table in tables:
            try:
                conn.execute(text(f"ANALYZE {table};"))
                conn.commit()
                print(f"✓ Analyzed table: {table}")
            except Exception as e:
                print(f"⚠ Warning analyzing {table}: {str(e)}")
    
    print("\n🎉 Database optimization complete!")

if __name__ == "__main__":
    apply_indexes()

