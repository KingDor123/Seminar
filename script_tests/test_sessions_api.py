import httpx
import asyncio
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:5001/api"

async def run_test():
    async with httpx.AsyncClient(timeout=10.0) as client:
        # 1. Register
        username = f"testuser_{random.randint(1000, 9999)}"
        password = "password123"
        email = f"{username}@example.com"
        
        logger.info(f"Step 1: Registering user {username}...")
        try:
            resp = await client.post(f"{BASE_URL}/auth/register", json={
                "username": username, "password": password, "email": email, "full_name": "Test User"
            })
            if resp.status_code != 201:
                logger.error(f"Registration failed: {resp.status_code} - {resp.text}")
                return
            
            user_data = resp.json().get("user")
            if not user_data:
                 logger.error(f"No user data in response: {resp.json()}")
                 return
                 
            user_id = user_data["id"]
            logger.info(f"Registered User ID: {user_id}")

            # 2. Login (to ensure cookies are set if register didn't, or just to verify login flow)
            logger.info("Step 2: Logging in...")
            resp = await client.post(f"{BASE_URL}/auth/login", json={
                "email": email, "password": password
            })
            if resp.status_code != 200:
                logger.error(f"Login failed: {resp.status_code} - {resp.text}")
                return
            
            # 3. Create Session
            logger.info("Step 3: Creating Session...")
            scenario_id = "job_interview"
            # Note: The backend currently accepts userId in body without auth check on this specific route, 
            # but we are authenticated via cookie now anyway.
            resp = await client.post(f"{BASE_URL}/chat/sessions", json={
                "userId": user_id,
                "scenarioId": scenario_id
            })
            if resp.status_code != 201:
                 logger.error(f"Create Session failed: {resp.status_code} - {resp.text}")
                 return
                 
            session_data = resp.json()
            session_id = session_data["id"]
            logger.info(f"Created Session ID: {session_id}")
            
            # 4. Get Sessions
            logger.info(f"Step 4: Fetching Sessions for user {user_id}...")
            resp = await client.get(f"{BASE_URL}/chat/users/{user_id}/sessions")
            if resp.status_code != 200:
                 logger.error(f"Get Sessions failed: {resp.status_code} - {resp.text}")
                 return

            sessions = resp.json()
            logger.info(f"Retrieved {len(sessions)} sessions.")
            
            # Validate
            if not isinstance(sessions, list):
                logger.error("Sessions response is not a list")
                return

            found = next((s for s in sessions if s["id"] == session_id), None)
            
            if found:
                logger.info("✅ Found created session in list.")
                logger.info(f"Session Data: {found}")
                if found["scenario_id"] == scenario_id and "start_time" in found:
                     logger.info("✅ Data validation passed.")
                else:
                     logger.error("❌ Data validation failed (missing fields or incorrect values).")
            else:
                logger.error(f"❌ Session {session_id} not found in user's session list.")

        except Exception as e:
            logger.error(f"Test Exception: {e}")

if __name__ == "__main__":
    asyncio.run(run_test())
