import re

def clean_executive_report(text: str) -> str:
    if not text:
        return ""

    # Remove repeated block symbols like ■ or ▣ etc.
    text = re.sub(r"[■□▪▢●◆◇]", "", text)

    # Remove double or broken ### headers
    text = re.sub(r"#+\s*#+", "###", text)

    # Fix section headers smashed into text
    text = re.sub(r"###\s*(Executive Audit Summary)", r"### Executive Audit Summary", text)
    text = re.sub(r"###\s*(Risk Factor Analysis)", r"### Risk Factor Analysis", text)
    text = re.sub(r"###\s*(Recommended Management Action)", r"### Recommended Management Action", text)

    # Remove header markers appearing mid-sentence
    text = re.sub(r"([a-z])###", r"\1\n\n###", text)

    # Ensure tables render properly
    text = re.sub(r"\|\s*:\-\-.*?\|\n", "| :---: | :--- | :--- |\n", text)

    # Trim excessive whitespace
    text = "\n".join([ln.strip() for ln in text.split("\n") if ln.strip()])

    return text
