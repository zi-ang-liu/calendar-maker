from typing import List

from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv
import os

from datetime import date


class Calendar(BaseModel):
    dtstart: str = Field(
        description="Start date and time of the event, in the format YYYYMMDDTHHMMSS; if all day, set it to T000000"
    )
    dtend: str = Field(
        description="End date and time of the event, in the format YYYYMMDDTHHMMSS; if all day, set it to dtstart + 1 day, T000000; otherwise, set it to dtstart + 2 hour"
    )
    summary: str = Field(description="Title of the event")
    description: str = Field(description="Description of the event")
    location: str = Field(description="Location of the event")
    link: str = Field(
        description="Link to the event, if contant contains a url; otherwise, leave blank."
    )

def get_weekday(day: date) -> str:
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return days[day.weekday()]

def llm(content: str) -> List[Calendar]:

    load_dotenv(".env")

    model = ChatOpenAI(openai_api_key=os.environ.get("OPENAI_API_KEY"), temperature=0)

    parser = JsonOutputParser(pydantic_object=Calendar)

    prompt = PromptTemplate(
        template="Create a calendar event, ensuring that the output maintains the same language as the input. If certain details are unavailable, they can be left as blank. \n{format_instructions}\n{content}. \n Current date, time and weekday are {today}, {weekday}",
        partial_variables={
            "format_instructions": parser.get_format_instructions(), 
            "weekday": get_weekday(date.today()), 
            "today": date.today().strftime("%Y%m%d")},
        input_variables=[content])

    chain = prompt | model | parser

    message = chain.invoke({"content": content})
    return message


def calendar2ics(calendar: Calendar) -> str:
    ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//hacksw/handcal//NONSGML v1.0//EN
BEGIN:VEVENT
DTSTART:{calendar['dtstart']}
DTEND:{calendar['dtend']}
SUMMARY:{calendar['summary']}
DESCRIPTION:{calendar['description']}
LOCATION:{calendar['location']}
URL:{calendar['link']}
END:VEVENT
END:VCALENDAR"""
    return ics


if __name__ == "__main__":
    # example content: "Create a calendar event for a meeting with John at 3pm at town hall on tomorrow. the access link is https://zoom.us/j/1234567890."
    content = ''
    print("Enter the content of the event. Press Enter twice to finish.")
    while True:
        line = input()
        if line == "":
            break
        content += line + "\n"

    print("Processing...")

    # content = 
    calendar = llm(content)
    print(calendar)
    ics = calendar2ics(calendar)

    # save ics to file
    with open("event.ics", "w") as f:
        f.write(ics)
