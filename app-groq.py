from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import time
import random
import pdfplumber
import re
import requests
import pytesseract
from PIL import Image
import io
import threading
import os
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# ===== Configuration Loading =====
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'backend', 'config.json')

if os.path.exists(CONFIG_PATH):
    print(f"Loading configuration from {CONFIG_PATH}")
    with open(CONFIG_PATH, 'r') as f:
        import json
        config_data = json.load(f)
        
    EMAIL = config_data.get("linkedin_email", "")
    PASSWORD = config_data.get("linkedin_password", "")
    CV_PATH = config_data.get("cv_path", "")
    GROQ_API_KEY = config_data.get("groq_api_key", "")
    
    USER_PREFERENCES = {
        "salary_expectation": config_data.get("salary_expectation", 0),
        "location": config_data.get("location", ""),
        "commuting": config_data.get("commuting", ""),
        "veteran_status": config_data.get("veteran_status", "No"),
        "disability": config_data.get("disability", "No"),
        "ethnicity": config_data.get("ethnicity", ""),
        "gender": config_data.get("gender", ""),
        "address": config_data.get("address", ""),
        "zip_code": config_data.get("zip_code", ""),
        "middle_name": config_data.get("middle_name", ""),
        "phone": config_data.get("phone", "")
    }
else:
    print("No config.json found. Reading from environment variables and defaults.")
    EMAIL = os.getenv("LINKEDIN_EMAIL", "")
    PASSWORD = os.getenv("LINKEDIN_PASSWORD", "")
    CV_PATH = os.getenv("CV_PATH", "")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    
    USER_PREFERENCES = {
        "salary_expectation": int(os.getenv("SALARY_EXPECTATION", 0)),
        "location": os.getenv("LOCATION", ""),
        "commuting": os.getenv("COMMUTING", ""),
        "veteran_status": os.getenv("VETERAN_STATUS", "No"),
        "disability": os.getenv("DISABILITY", "No"),
        "ethnicity": os.getenv("ETHNICITY", ""),
        "gender": os.getenv("GENDER", ""),
        "address": os.getenv("ADDRESS", ""),
        "zip_code": os.getenv("ZIP_CODE", ""),
        "middle_name": os.getenv("MIDDLE_NAME", ""),
        "phone": os.getenv("PHONE", "")
    }

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

# =================================================

def human_delay(min_seconds=1, max_seconds=3):
    """Simulate human-like delay with randomization."""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)
    return delay

def typing_delay(text_length):
    """Calculate realistic typing delay based on text length.
    Average human types 40-60 words per minute (3-5 chars/second)."""
    chars_per_second = random.uniform(3, 5)
    delay = text_length / chars_per_second
    # Add some randomness (pauses while thinking)
    delay *= random.uniform(1.0, 1.5)
    time.sleep(delay)
    return delay

def fill_like_human(field, text):
    """Fill a field with human-like typing simulation."""
    field.click()  # Click to focus
    time.sleep(random.uniform(0.2, 0.5))  # Slight pause after clicking
    
    # Clear existing content slowly if any
    current = field.input_value()
    if current:
        field.fill("")
        time.sleep(random.uniform(0.3, 0.7))
    
    # Type character by character with variable speed
    for i, char in enumerate(text):
        field.fill(text[:i+1])
        # Random delay between keystrokes (0.05 to 0.25 seconds)
        time.sleep(random.uniform(0.05, 0.25))
        
        # Occasional longer pauses (simulating thinking)
        if random.random() < 0.15:  # 15% chance
            time.sleep(random.uniform(0.5, 1.5))
    
    # Short pause after finishing typing
    time.sleep(random.uniform(0.3, 0.8))

# Extract text from CV PDF
def extract_cv_text(pdf_path):
    """Extract text from the CV PDF."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            cv_text = ""
            for page in pdf.pages:
                cv_text += page.extract_text() or ""
        return cv_text
    except Exception as e:
        print(f"Error extracting CV text: {e}")
        return ""

CV_TEXT = extract_cv_text(CV_PATH)
if not CV_TEXT:
    raise ValueError("CV text extraction failed. Please check the PDF path and content.")

# Local LLM client function
def call_local_llm(prompt, system_prompt="You are a helpful assistant for job applications."):
    """Call the Groq API."""
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",  # or "mixtral-8x7b-32768" or "llama-3.1-70b-versatile"
            temperature=0.1,
            max_tokens=100,
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error calling Groq API: {e}")
        return None

# OCR function to read text from screenshots
def ocr_screenshot(page, element=None):
    """Take screenshot and extract text using OCR."""
    try:
        if element:
            screenshot_bytes = element.screenshot()
        else:
            screenshot_bytes = page.screenshot()
        
        image = Image.open(io.BytesIO(screenshot_bytes))
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        print(f"Error performing OCR: {e}")
        return ""

# Track processed jobs
processed_jobs = set()
applied_jobs = set()

def is_specific_question(question, keywords):
    """Check if the question contains any of the keywords."""
    return any(keyword.lower() in question.lower() for keyword in keywords)

def get_specific_response(question):
    """Return hardcoded response for specific questions."""
    question_lower = question.lower()
    if is_specific_question(question, ["veteran", "military"]):
        return USER_PREFERENCES["veteran_status"]
    elif is_specific_question(question, ["disability", "disabled"]):
        return USER_PREFERENCES["disability"]
    elif is_specific_question(question, ["ethnicity", "race"]):
        return USER_PREFERENCES["ethnicity"]
    elif is_specific_question(question, ["gender"]):
        return USER_PREFERENCES["gender"]
    elif is_specific_question(question, ["location", "commute", "relocate", "address"]):
        return USER_PREFERENCES["address"]
    elif is_specific_question(question, ["phone", "mobile", "contact number"]):
        return USER_PREFERENCES["phone"]
    elif is_specific_question(question, ["zip", "postal"]):
        return USER_PREFERENCES["zip_code"]
    return None

def get_llm_response(question, previous_response=None, error_message=None):
    """Get a response from local LLM for text fields."""
    specific_response = get_specific_response(question)
    if specific_response:
        print(f"Using hardcoded response for '{question}': {specific_response}")
        return specific_response

    question_lower = question.lower()
    numerical_keywords = ["year", "years", "experience", "how many", "number of"]
    is_numerical = any(keyword in question_lower for keyword in numerical_keywords)

    if is_numerical:
        experience_pattern = r"(\d+)\s*(?:year|years)\s*(?:of\s*experience|in\s*\w+)"
        matches = re.findall(experience_pattern, CV_TEXT.lower())
        if matches:
            years = max(int(match) for match in matches)
            print(f"Found {years} years of experience in CV for '{question}'")
            return str(years)
        else:
            print(f"No experience found in CV for '{question}'. Defaulting to 4.")
            return "4"

    prompt = (
        f"Based on this CV: '{CV_TEXT[:1000]}...', and user preferences: "
        f"salary: ${USER_PREFERENCES['salary_expectation']}, location: {USER_PREFERENCES['location']}, "
    )
    
    if error_message and previous_response:
        prompt += (
            f"Previous answer '{previous_response}' caused error: '{error_message}'. "
            f"Provide a corrected answer. "
        )
    
    prompt += (
        f"Question: '{question}'. "
        f"Provide ONLY the answer (number for experience, Yes/No for yes/no questions, "
        f"short text for others). No explanation."
    )
    
    response = call_local_llm(prompt)
    print(f"LLM response for '{question}': {response}")
    return response if response else ("4" if is_numerical else "Not specified")

def get_llm_selection(question, options, previous_response=None, error_message=None):
    """Get the best option from LLM for dropdowns, radio buttons, etc."""
    specific_response = get_specific_response(question)
    if specific_response and specific_response in options:
        print(f"Using hardcoded selection for '{question}': {specific_response}")
        return specific_response

    prompt = (
        f"Based on CV and preferences, select the BEST option for: '{question}'\n"
        f"Options: {', '.join(options)}\n"
    )
    
    if error_message and previous_response:
        prompt += f"Previous '{previous_response}' caused error: '{error_message}'. Choose different option.\n"
    
    prompt += "Return ONLY the exact option text, nothing else."
    
    response = call_local_llm(prompt)
    
    if response and response in options:
        print(f"LLM selected: {response}")
        return response
    
    # Fuzzy match
    for option in options:
        if response and response.lower() in option.lower():
            print(f"LLM fuzzy matched: {option}")
            return option
    
    print(f"LLM selection failed, using first option: {options[0]}")
    return options[0]

def fill_text_fields(page, modal):
    """Fill text fields using LLM and OCR with human-like timing."""
    try:
        text_inputs = modal.locator("input[type='text'], textarea").all()
        
        for field in text_inputs:
            if not field.is_visible() or not field.is_enabled():
                continue
            
            current_value = field.input_value()
            if current_value.strip():
                continue
            
            # Try to find label
            question = "Unknown question"
            try:
                label = field.locator("xpath=./preceding::label[1]").first
                if label.is_visible():
                    question = label.inner_text().strip()
                else:
                    ocr_text = ocr_screenshot(page, field)
                    if ocr_text:
                        question = ocr_text
            except:
                ocr_text = ocr_screenshot(page, field)
                if ocr_text:
                    question = ocr_text
            
            print(f"Filling field for: '{question}'")
            answer = get_llm_response(question)
            
            # ✅ HUMAN-LIKE TYPING instead of instant fill
            fill_like_human(field, answer)
            
            # ✅ LONGER, RANDOM delay after filling
            human_delay(1.5, 3.5)
            
            # Check for errors
            error_msgs = modal.locator(".artdeco-inline-feedback__message").all()
            retry_count = 0
            max_retries = 3
            
            while error_msgs and retry_count < max_retries:
                error_text = error_msgs[0].inner_text()
                print(f"Error detected: {error_text}")
                
                # ✅ Pause before correcting (human would read error first)
                human_delay(2, 4)
                
                corrected = get_llm_response(question, answer, error_text)
                fill_like_human(field, corrected)
                
                human_delay(1.5, 3)
                
                error_msgs = modal.locator(".artdeco-inline-feedback__message").all()
                retry_count += 1
                answer = corrected
            
            print(f"Filled '{question}' with '{answer}'")
    
    except Exception as e:
        print(f"Error filling text fields: {e}")

def handle_dropdowns(page, modal):
    """Handle dropdown selections with human-like timing."""
    try:
        dropdowns = modal.locator("select").all()
        
        for dropdown in dropdowns:
            if not dropdown.is_visible() or not dropdown.is_enabled():
                continue
            
            current = dropdown.input_value()
            if current and current.lower() not in ["", "select an option", "none"]:
                continue
            
            # Get question...
            question = "Unknown question"
            try:
                label = dropdown.locator("xpath=./preceding::label[1]").first
                if label.is_visible():
                    question = label.inner_text().strip()
                else:
                    ocr_text = ocr_screenshot(page, dropdown)
                    if ocr_text:
                        question = ocr_text
            except:
                ocr_text = ocr_screenshot(page, dropdown)
                if ocr_text:
                    question = ocr_text
            
            # Get options...
            options = []
            option_elements = dropdown.locator("option").all()
            for opt in option_elements:
                text = opt.inner_text().strip()
                if text and text.lower() != "select an option":
                    options.append(text)
            
            if not options:
                continue
            
            # ✅ Pause before interacting (human would read options)
            human_delay(1, 2.5)
            
            # Click to open dropdown
            dropdown.click()
            human_delay(0.5, 1.5)  # Pause while "reading" options
            
            selected = get_llm_selection(question, options)
            dropdown.select_option(label=selected)
            print(f"Selected '{selected}' for '{question}'")
            
            # ✅ LONGER delay after selection
            human_delay(1.5, 3)
    
    except Exception as e:
        print(f"Error handling dropdowns: {e}")

def handle_radio_buttons(page, modal):
    """Handle radio buttons with human-like timing."""
    try:
        radios = modal.locator("input[type='radio']").all()
        radio_groups = {}

        for radio in radios:
            name = radio.get_attribute("name")
            if name:
                radio_groups.setdefault(name, []).append(radio)

        for name, group in radio_groups.items():
            if any(r.is_checked() for r in group):
                continue

            # Get question and options...
            question = "Unknown question"
            try:
                legend = group[0].locator("xpath=./preceding::legend[1]").first
                if legend.is_visible():
                    question = legend.inner_text().strip()
                else:
                    ocr_text = ocr_screenshot(page, group[0])
                    if ocr_text:
                        question = ocr_text
            except:
                ocr_text = ocr_screenshot(page, group[0])
                if ocr_text:
                    question = ocr_text

            options = []
            labels = []

            for radio in group:
                try:
                    label = radio.locator("xpath=following-sibling::label[1]").first
                    if label.is_visible():
                        options.append(label.inner_text().strip())
                        labels.append(label)
                except:
                    pass

            if not options:
                continue

            # ✅ Pause to "read" the question and options
            human_delay(1.5, 3)

            selected_option = get_llm_selection(question, options)
            print(f"Choosing '{selected_option}' for '{question}'")

            for i, opt in enumerate(options):
                if opt.strip().lower() == selected_option.strip().lower():
                    try:
                        labels[i].scroll_into_view_if_needed()
                        # ✅ Small delay before clicking
                        time.sleep(random.uniform(0.3, 0.8))
                        labels[i].click(force=True)
                        print(f"Clicked label for '{opt}'")
                    except:
                        try:
                            group[i].scroll_into_view_if_needed()
                            time.sleep(random.uniform(0.3, 0.8))
                            group[i].click(force=True)
                            print(f"Clicked radio input for '{opt}'")
                        except Exception as e:
                            print(f"Failed to click option '{opt}': {e}")
                    break

            # ✅ LONGER delay after clicking
            human_delay(1.5, 3)

    except Exception as e:
        print(f"Error handling radio buttons: {e}")


def handle_checkboxes(page, modal):
    """Handle checkboxes with human-like timing."""
    try:
        checkboxes = modal.locator("input[type='checkbox']").all()
        print(f"Found {len(checkboxes)} checkboxes")

        for checkbox in checkboxes:
            if not checkbox.is_visible() or not checkbox.is_enabled():
                continue

            checked = checkbox.is_checked()
            if checked:
                continue

            # Get label...
            question = "Unknown checkbox"
            label_text = ""

            try:
                label = checkbox.locator("xpath=following-sibling::label[1]").first
                if label.is_visible():
                    label_text = label.inner_text().strip()
                    question = label_text
                else:
                    ocr_text = ocr_screenshot(page, checkbox)
                    if ocr_text:
                        label_text = ocr_text
                        question = ocr_text
            except Exception:
                ocr_text = ocr_screenshot(page, checkbox)
                if ocr_text:
                    label_text = ocr_text
                    question = ocr_text

            print(f"Processing checkbox: '{question}'")

            # ✅ Pause to "read" the checkbox label
            human_delay(1, 2)

            # Decide whether to check it...
            should_check = False
            if any(keyword in question.lower() for keyword in ["consent", "agree", "accept", "yes", "confirm"]):
                should_check = True
            else:
                prompt = (
                    f"Given this question or label: '{question}', "
                    f"should the applicant check this box during a job application? "
                    f"Answer 'yes' or 'no' only."
                )
                response = call_local_llm(prompt)
                should_check = response and response.lower().startswith("y")

            if should_check:
                try:
                    checkbox.scroll_into_view_if_needed()
                    # ✅ Small delay before clicking
                    time.sleep(random.uniform(0.3, 0.8))
                    checkbox.click(force=True)
                    print(f"✅ Checked box for '{label_text}'")
                    # ✅ LONGER delay after checking
                    human_delay(1.5, 3)
                except Exception as e:
                    print(f"❌ Failed to click checkbox '{label_text}': {e}")
            else:
                print(f"Skipping checkbox '{label_text}'")

    except Exception as e:
        print(f"Error handling checkboxes: {e}")


def is_job_already_applied(job_element):
    """Check if job has already been applied to."""
    try:
        text = job_element.inner_text().lower()
        return "applied" in text and ("day" in text or "week" in text)
    except:
        return False

def find_next_button_with_ocr(page):
    """Use OCR to find and click the Next button in pagination."""
    try:
        print("🔍 Searching for pagination buttons using OCR...")
        
        # Take screenshot of bottom of page where pagination usually is
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)
        
        # Get pagination area
        pagination_selectors = [
            ".artdeco-pagination",
            ".jobs-search-results-list__pagination",
            "[data-test-pagination]",
            "nav[aria-label*='pagination' i]",
            ".jobs-search-pagination"
        ]
        
        pagination_element = None
        for selector in pagination_selectors:
            try:
                pagination_element = page.locator(selector).first
                if pagination_element.is_visible():
                    print(f"✅ Found pagination element: {selector}")
                    break
            except:
                continue
        
        if not pagination_element:
            # Fallback: screenshot bottom portion of page
            print("📸 Taking screenshot of page bottom for OCR...")
            screenshot_bytes = page.screenshot()
            image = Image.open(io.BytesIO(screenshot_bytes))
            
            # Crop bottom 20% of image where pagination usually is
            width, height = image.size
            cropped = image.crop((0, int(height * 0.8), width, height))
            ocr_text = pytesseract.image_to_string(cropped)
            print(f"OCR detected text: {ocr_text}")
        else:
            # OCR the pagination element
            ocr_text = ocr_screenshot(page, pagination_element)
            print(f"OCR pagination text: {ocr_text}")
        
        # Try multiple button selectors
        next_button_selectors = [
            "button[aria-label*='Next' i]",
            "button[aria-label*='next page' i]",
            "button:has-text('Next')",
            "li.artdeco-pagination__indicator--number.active + li button",
            "button.artdeco-pagination__button--next",
            "[data-test-pagination-next]"
        ]
        
        for selector in next_button_selectors:
            try:
                next_btn = page.locator(selector).first
                if next_btn.is_visible() and next_btn.is_enabled():
                    # Check if button is not disabled
                    is_disabled = next_btn.get_attribute("disabled")
                    if is_disabled:
                        print(f"⚠️ Button found but disabled: {selector}")
                        continue
                    
                    next_btn.scroll_into_view_if_needed()
                    next_btn.click()
                    print(f"✅ Clicked Next button using selector: {selector}")
                    return True
            except Exception as e:
                print(f"❌ Failed with selector {selector}: {e}")
                continue
        
        # Fallback: Use OCR coordinates to click
        if "next" in ocr_text.lower():
            print("⚠️ Next button detected in OCR but couldn't click with selectors")
            # Try clicking any visible button elements
            all_buttons = page.locator("button").all()
            for btn in all_buttons:
                try:
                    if btn.is_visible():
                        btn_text = btn.inner_text().lower()
                        if "next" in btn_text and "previous" not in btn_text:
                            btn.scroll_into_view_if_needed()
                            btn.click()
                            print(f"✅ Clicked button with text: {btn_text}")
                            return True
                except:
                    continue
        
        print("❌ No Next button found")
        return False
        
    except Exception as e:
        print(f"❌ Error finding next button: {e}")
        return False

def go_to_next_page(page):
    """Navigate to next page of results with multiple fallback methods."""
    try:
        print("\n🔄 Attempting to navigate to next page...")
        
        # Store current URL to verify navigation
        current_url = page.url
        current_page_num = extract_page_number(current_url)
        print(f"Current page: {current_page_num}, URL: {current_url}")
        
        # Method 1: Standard Next button
        success = find_next_button_with_ocr(page)
        
        if success:
            time.sleep(5)
            new_url = page.url
            new_page_num = extract_page_number(new_url)
            
            if new_url != current_url or new_page_num > current_page_num:
                print(f"✅ Successfully navigated to page {new_page_num}")
                return True
            else:
                print("⚠️ Button clicked but page didn't change")
        
        # Method 2: Try URL parameter manipulation
        print("🔧 Trying URL manipulation...")
        if "&start=" in current_url:
            # LinkedIn uses &start=25, &start=50, etc.
            match = re.search(r'&start=(\d+)', current_url)
            if match:
                current_start = int(match.group(1))
                next_start = current_start + 25
                new_url = re.sub(r'&start=\d+', f'&start={next_start}', current_url)
                page.goto(new_url)
                print(f"✅ Navigated via URL to start={next_start}")
                time.sleep(5)
                return True
        else:
            # Add start parameter
            separator = "&" if "?" in current_url else "?"
            new_url = f"{current_url}{separator}start=25"
            page.goto(new_url)
            print(f"✅ Added start parameter to URL")
            time.sleep(5)
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Error navigating to next page: {e}")
        return False

def extract_page_number(url):
    """Extract page number from URL."""
    match = re.search(r'&start=(\d+)', url)
    if match:
        start_value = int(match.group(1))
        return (start_value // 25) + 1
    return 1

def run_automation():
    """Main function that runs in a separate thread."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # Login
            print("Logging in to LinkedIn...")
            page.goto("https://www.linkedin.com/login")
            page.fill("#username", EMAIL)
            page.fill("#password", PASSWORD)
            page.click("button[type='submit']")
            time.sleep(5)
            print("Logged in successfully")
            
            # Navigate to job search
            search_url = "https://www.linkedin.com/jobs/search/?keywords=machine%20learning%20intern&location=Silicon%20Valley%2C%20California&f_AL=true&f_TPR=r604800"
            page.goto(search_url)
            time.sleep(5)
            
            job_counter = 0
            page_number = 1
            max_pages = 10
            
            while page_number <= max_pages:
                print(f"\n{'='*60}")
                print(f"📄 PROCESSING PAGE {page_number}")
                print(f"{'='*60}")
                
                no_new_jobs = 0
                max_no_new_attempts = 3
                
                while no_new_jobs < max_no_new_attempts:
                    # Scroll to load jobs
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(3)
                    
                    job_listings = page.locator(".job-card-container").all()
                    
                    if not job_listings:
                        print("⚠️ No job listings found, scrolling and retrying...")
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        time.sleep(5)
                        job_listings = page.locator(".job-card-container").all()
                        if not job_listings:
                            print("❌ Still no jobs found, breaking...")
                            break
                    
                    print(f"📋 Found {len(job_listings)} job cards on page")
                    found_new = False
                    
                    for job in job_listings:
                        try:
                            job_link = job.locator("a").first
                            href = job_link.get_attribute("href")
                            if not href:
                                continue
                            
                            job_id = href.split("?")[0]
                            
                            if job_id in processed_jobs:
                                continue
                            
                            processed_jobs.add(job_id)
                            found_new = True
                            
                            if is_job_already_applied(job):
                                print(f"⏭️ Skipping {job_id} (already applied)")
                                continue
                            
                            job_counter += 1
                            print(f"\n{'='*50}")
                            print(f"💼 Applying to job {job_counter} ({job_id})...")
                            print(f"{'='*50}")
                            
                            # Click job
                            job_link.scroll_into_view_if_needed()
                            job_link.click()
                            time.sleep(2)
                            
                            # Click Easy Apply
                            try:
                                easy_apply = page.locator(".jobs-apply-button").first
                                easy_apply.click(timeout=15000)
                                print("✅ Clicked Easy Apply")
                                # ✅ LONGER wait for modal to appear naturally
                                human_delay(3, 5)
                            except:
                                print("❌ Easy Apply not found")
                                continue
                            
                            # Wait for modal
                            modal = page.locator(".artdeco-modal").first
                            modal.wait_for(timeout=10000)
                            
                            max_steps = 10
                            step_count = 0
                            
                            while step_count < max_steps:
                                print(f"🔍 Step {step_count + 1}...")
                                
                                # ✅ Pause before starting each step (human would scan the form)
                                human_delay(2, 4)
                                
                                # Fill phone
                                try:
                                    phone = modal.locator("input[id*='phone']").first
                                    if phone.is_visible():
                                        fill_like_human(phone, USER_PREFERENCES["phone"])
                                        human_delay(1, 2)
                                except:
                                    pass
                                
                                # Fill zip
                                try:
                                    zip_field = modal.locator("input[id*='zip']").first
                                    if zip_field.is_visible():
                                        fill_like_human(zip_field, USER_PREFERENCES["zip_code"])
                                        human_delay(1, 2)
                                except:
                                    pass
                                
                                fill_text_fields(page, modal)
                                handle_dropdowns(page, modal)
                                handle_radio_buttons(page, modal)
                                handle_checkboxes(page, modal)
                                
                                # Try clicking buttons
                                clicked = False
                                for btn_text in ["submit", "apply", "review", "next"]:
                                    try:
                                        button = modal.locator(f"button:has-text('{btn_text}')").first
                                        if button.is_visible() and button.is_enabled():
                                            # ✅ Scroll to button smoothly
                                            button.scroll_into_view_if_needed()
                                            # ✅ Pause before clicking (human would review)
                                            human_delay(2, 4)
                                            button.click()
                                            print(f"✅ Clicked {btn_text}")
                                            clicked = True
                                            
                                            if btn_text in ["submit", "apply"]:
                                                # ✅ LONGER wait after submitting
                                                human_delay(4, 7)
                                                try:
                                                    done = page.locator("button:has-text('Done')").first
                                                    done.click(timeout=10000)
                                                    print("✅ Clicked Done")
                                                except:
                                                    pass
                                            break
                                    except:
                                        continue
                                
                                if not clicked:
                                    print("⚠️ No buttons to click")
                                    break
                                
                                # ✅ LONGER delay between steps
                                human_delay(3, 6)
                                step_count += 1
                            
                            applied_jobs.add(job_id)
                            print(f"✅ Successfully applied to job {job_id}")
                            
                            # Close modal
                            try:
                                page.keyboard.press("Escape")
                                time.sleep(2)
                            except:
                                pass

                            # Add random delay to avoid detection
                            # ✅ MUCH LONGER random delay
                            delay = random.uniform(15, 45)  # 15-45 seconds instead of 5-15
                            print(f"⏳ Waiting {delay:.2f} seconds before next application...")
                            time.sleep(delay)
                        
                        except Exception as e:
                            print(f"❌ Error with job: {e}")
                            continue
                    
                    if not found_new:
                        no_new_jobs += 1
                        print(f"⚠️ No new jobs found ({no_new_jobs}/{max_no_new_attempts})")
                    else:
                        no_new_jobs = 0
                    
                    # Scroll again
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(3)
                
                print(f"\n✅ Completed processing page {page_number}")
                print(f"📊 Total jobs applied: {len(applied_jobs)}")
                print(f"📊 Total jobs processed: {len(processed_jobs)}")
                
                # Navigate to next page
                if page_number < max_pages:
                    if go_to_next_page(page):
                        page_number += 1
                        
                        # Wait for new page to load
                        time.sleep(8)
                        
                        # Verify page loaded
                        try:
                            page.wait_for_selector(".job-card-container", timeout=15000)
                            print(f"✅ Successfully loaded page {page_number}")
                        except:
                            print("⚠️ Timeout waiting for job cards, but continuing...")
                        
                        # Trigger lazy loading
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        time.sleep(4)
                        
                    else:
                        print("❌ Could not navigate to next page. Ending automation.")
                        break
                else:
                    print("✅ Reached maximum page limit")
                    break

        except KeyboardInterrupt:
            print("\n⚠️ Stopped by user")
        except Exception as e:
            print(f"❌ Fatal error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print(f"\n{'='*60}")
            print(f"📊 FINAL STATISTICS")
            print(f"{'='*60}")
            print(f"✅ Successfully applied to: {len(applied_jobs)} jobs")
            print(f"📋 Total jobs processed: {len(processed_jobs)} jobs")
            print(f"{'='*60}")
            browser.close()

# For Jupyter notebook - run in separate thread
def start_automation():
    """Start automation in a separate thread to avoid event loop conflicts."""
    thread = threading.Thread(target=run_automation)
    thread.start()
    return thread

# Run this in Jupyter:
# thread = start_automation()
# To check if still running: thread.is_alive()

if __name__ == "__main__":
    # For standalone script
    run_automation()