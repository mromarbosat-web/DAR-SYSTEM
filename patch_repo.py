import re

with open("bot/database/repositories/economy_repository.py", "r") as f:
    content = f.read()

def replacer(match):
    body = match.group(1)
    
    # Remove the existing try-commit-except block
    body = re.sub(r'\n\s*try:\n\s*await self\.session\.commit\(\)\n\s*except Exception:\n\s*await self\.session\.rollback\(\)\n\s*await self\.session\.flush\(\)', '', body)
    
    # Replace async with self.session.begin_nested():
    new_block = f"""
        try:{body}
            await self.session.commit()
        except Exception as e:
            logger.error(f"Error in atomic operation: {{e}}")
            await self.session.rollback()
            raise e
"""
    return new_block

# But actually, the return statement is INSIDE the async with block!
