# Akkiai_crew

This branch updated on 17th Feb 2025.

NEW UPDATE-- TEST-- Seperated /chat and /upsert endpoints and no push from chat endpoint (only fetch from RAG)
 
1. Added crew 1-9 for production
2. Output pydantic only done for crew 1 and 9, have to do for others
3. updated the directory of codes
4. Inputs limited only to STARTUP_INFO
5. updated the main.py with orchestration of crew runs
6. Added CHAT endpoint with anthropic API stateless
7. Text preprocessing to remove unwanted spaces or characters and passed that processed text to other llm to re validate the json format
8. Updated the config files, it now takes inputs only once. Changed pydantic a bit (Not for Production)
9. Added Pinecone Vector DB for Personalised Chat for each entity_id (namespace) user/project --TEST--
10. Added Permanent Temporary and Character Pinecone RAG and implemented no duplicate records to Pinecone---TEST---