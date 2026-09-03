from services.ai_service import analyze_issue

result = analyze_issue(
    "AC not working",
    "The AC is turned on but it is not cooling the room."
)

print("\nAI ANALYSIS:")
print(result)