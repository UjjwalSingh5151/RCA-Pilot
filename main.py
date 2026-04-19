import anthropic
import os

client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY")
)

def analyse_metric(situation):
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""You are a business analyst at an Indian e-commerce company.
                
A business metric situation has been flagged:
{situation}

Give me:
1. Top 3 root cause hypotheses (most likely first)
2. What data I need to verify each hypothesis
3. Recommended first action

Be specific and concise."""
            }
        ]
    )
    return message.content[0].text

print("=== Growth Analytics Co-pilot ===")
print("Describe your metric situation (press Enter twice when done):")

lines = []
while True:
    line = input()
    if line == "":
        break
    lines.append(line)

situation = "\n".join(lines)
result = analyse_metric(situation)
print("\n" + result)