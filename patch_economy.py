import re

with open("bot/database/repositories/economy_repository.py", "r") as f:
    code = f.read()

# Replace `async with self.session.begin_nested():` with `try:`
code = code.replace("async with self.session.begin_nested():", "try:")

# Remove the try...except...commit blocks
commit_block = """            try:
                await self.session.commit()
            except Exception:
                await self.session.rollback()
                await self.session.flush()"""
code = code.replace(commit_block, "            await self.session.commit()")

commit_block_2 = """            try:
                await self.session.commit()
            except Exception:
                await self.session.rollback()
                await self.session.flush()"""

# We also need to add except Exception at the end of the functions? 
# Wait, if we use `try:`, we MUST have an `except:` block!
