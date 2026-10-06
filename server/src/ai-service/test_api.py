import os
from dotenv import load_dotenv
from imagine import ChatMessage, ImagineClient

load_dotenv()

client = ImagineClient(
    api_key=os.getenv("IMAGINE_API_KEY"),
    endpoint=os.getenv("IMAGINE_API_ENDPOINT")
)

text = "The team meeting discussed the upcoming hackathon project. Rahul will complete the backend API by Friday. Priya will prepare the presentation. The documentation needs to be completed before the final demo. The team decided to use artificial intelligence to automate note summarization."

prompt = (
    "You are a meeting-notes summarization assistant.\n\n"
    "Analyze the notes below and provide a structured summary using EXACTLY these section headers:\n\n"
    "SUMMARY:\n(Write a concise overall summary here)\n\n"
    "KEY POINTS:\n- (list each key point on its own line, prefixed with a dash)\n\n"
    "ACTION ITEMS:\n- Task: [task description] | Responsible: [person or Not specified] | Deadline: [deadline or Not specified] | Priority: [High/Medium/Low]\n\n"
    "DECISIONS:\n- (list each decision on its own line, prefixed with a dash)\n\n"
    "PENDING QUESTIONS:\n- (list each question on its own line, prefixed with a dash)\n\n"
    "If a section has no items, write 'None' after the header.\n\n"
    f"NOTES:\n{text}"
)

response = client.chat(
    messages=[ChatMessage(role="user", content=prompt)],
    model="Llama-3.1-8B",
    max_tokens=2048,
    temperature=0.2,
)

content = response.choices[0].message.content
print(f"Content repr: {repr(content)}")
print(f"\n===== RAW CONTENT =====")
print(content)
print(f"\n===== LINE BY LINE =====")
for i, line in enumerate(content.split("\n")):
    print(f"  {i}: {repr(line)}")
