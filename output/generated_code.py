```python
from datetime import datetime
import pytz

def show_time_in_la():
    try:
        # Get the current UTC time
        utc_now = datetime.now(pytz.utc)
        
        # Convert to Pacific Time
        pacific_time = utc_now.astimezone(pytz.timezone('America/Los_Angeles'))
        
        # Format the time in a user-friendly way
        formatted_time = pacific_time.strftime('%I:%M %p')
        
        return formatted_time
    except Exception as e:
        return f"An error occurred: {e}"

# Example usage
if __name__ == "__main__":
    print(show_time_in_la())
```