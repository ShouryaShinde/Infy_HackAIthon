import os
from dotenv import load_dotenv
from imagine import ChatMessage, ImagineClient

load_dotenv()

api_key = os.getenv("IMAGINE_API_KEY")
endpoint = os.getenv("IMAGINE_API_ENDPOINT")

if not api_key:
    raise ValueError("IMAGINE_API_KEY is not set in .env")
if not endpoint:
    raise ValueError("IMAGINE_API_ENDPOINT is not set in .env")

client = ImagineClient(
    api_key=api_key,
    endpoint=endpoint
)


def summarize_text(text):

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

    chat_response = client.chat(
        messages=[
            ChatMessage(
                role="user",
                content=prompt
            )
        ],
        model="Llama-3.1-8B",
        max_tokens=2048,
        temperature=0.2,
    )

    print("\n===== CHAT RESPONSE OBJECT =====")
    print(chat_response)

    # Extract content from the OpenAI-compatible response structure
    if not chat_response.choices or len(chat_response.choices) == 0:
        raise ValueError("AI returned no choices in the response")

    content = chat_response.choices[0].message.content

    print("\n===== EXTRACTED CONTENT =====")
    print(repr(content))

    if not content or not content.strip():
        raise ValueError("AI returned empty content")

    # Parse the structured text response into a JSON-compatible dictionary
    return parse_summary_response(content)


def parse_summary_response(text):
    """Parse the AI's structured text response into a dictionary."""

    sections = {
        "summary": "",
        "keyPoints": [],
        "actionItems": [],
        "decisions": [],
        "pendingQuestions": []
    }

    current_section = None
    lines = text.strip().split("\n")

    for line in lines:
        stripped = line.strip()

        if not stripped:
            continue

        # Detect section headers (strip markdown bold ** and trailing colons)
        upper = stripped.strip("*").strip().upper().rstrip(":")
        if upper in ("SUMMARY", "CONCISE SUMMARY"):
            current_section = "summary"
            # Check if summary is on the same line as the header
            raw_after = stripped.strip("*").strip()
            after_colon = raw_after.split(":", 1)
            if len(after_colon) > 1 and after_colon[1].strip():
                sections["summary"] = after_colon[1].strip()
            continue
        elif upper in ("KEY POINTS", "KEYPOINTS", "KEY POINT"):
            current_section = "keyPoints"
            continue
        elif upper in ("ACTION ITEMS", "ACTION ITEM", "ACTIONITEMS"):
            current_section = "actionItems"
            continue
        elif upper in ("DECISIONS", "IMPORTANT DECISIONS"):
            current_section = "decisions"
            continue
        elif upper in ("PENDING QUESTIONS", "QUESTIONS", "UNRESOLVED QUESTIONS"):
            current_section = "pendingQuestions"
            continue
        elif upper in ("NOTES",):
            # Model sometimes echoes back the notes — ignore this section
            current_section = None
            continue

        clean_check = stripped.lstrip("-•* ").strip()
        if clean_check.lower() == "none":
            continue

        # Parse content based on current section
        if current_section == "summary":
            item = stripped.lstrip("-•*").strip()
            if item:
                if sections["summary"]:
                    sections["summary"] += " " + item
                else:
                    sections["summary"] = item

        elif current_section == "keyPoints":
            item = stripped.lstrip("-•*").strip()
            if item:
                sections["keyPoints"].append(item)

        elif current_section == "actionItems":
            item = stripped.lstrip("-•*").strip()
            if item:
                action = parse_action_item(item)
                sections["actionItems"].append(action)

        elif current_section == "decisions":
            item = stripped.lstrip("-•*").strip()
            if item:
                sections["decisions"].append(item)

        elif current_section == "pendingQuestions":
            item = stripped.lstrip("-•*").strip()
            if item:
                sections["pendingQuestions"].append(item)

    return sections


def parse_action_item(text):
    """Parse an action item line into a structured dictionary."""

    action = {
        "task": text,
        "responsible": "Not specified",
        "deadline": "Not specified",
        "priority": "Medium"
    }

    # Try to parse structured format: Task: ... | Responsible: ... | Deadline: ... | Priority: ...
    if "|" in text:
        parts = text.split("|")
        for part in parts:
            part = part.strip()
            lower = part.lower()

            if lower.startswith("task:"):
                action["task"] = part.split(":", 1)[1].strip()
            elif lower.startswith("responsible:"):
                action["responsible"] = part.split(":", 1)[1].strip()
            elif lower.startswith("deadline:"):
                action["deadline"] = part.split(":", 1)[1].strip()
            elif lower.startswith("priority:"):
                action["priority"] = part.split(":", 1)[1].strip()

    return action


