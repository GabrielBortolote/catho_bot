# built in imports
import time
import re

# dependency imports
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    ElementNotInteractableException,
    StaleElementReferenceException,
)

# local imports
from credentials import user, password
from urls import login, searches

# constants
NPTE = 'Not possible to extract'

def bot():
    driver = webdriver.Chrome()
    driver.maximize_window()

    # access login page
    driver.get(login)

    # perform login
    el = driver.find_element(By.XPATH, '//input[@name="email"]')
    el.send_keys(user)

    el = driver.find_element(By.XPATH, '//input[@name="password"]')
    el.send_keys(password)

    el = driver.find_element(By.XPATH, '//button[@type="submit"]')
    el.click()

    # check if login was done
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, '//span[text()="Perfil"]'))
    )

    # search loop
    print("%d searches registered, starting execution" % len(searches))
    roles = []
    banner_closed = False
    for search_index, search in enumerate(searches):

        print('-'*50)
        print('Search number %d' % (search_index + 1))

        attempts = 0
        load_search_error = False
        while True:
            try:
                # go to search link
                driver.get(search)

                # wait for search list
                search_result = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, 'search-result'))
                )

            except TimeoutException as exc:
                attempts += 1
                if attempts > 3:
                    print('Not possible to load this search')
                    load_search_error = True

            else:
                break

        # if error on loading go to the next search
        if load_search_error: continue

        # page loop
        page_counter = 0
        while True:

            # close banner
            if not banner_closed:
                try:
                    el = driver.find_element(By.XPATH, '//div[@class="container-close-app-banner"]')
                    el.click()
                except NoSuchElementException:
                    pass
                banner_closed = True

            # apply for the roles
            search_result = driver.find_element(By.ID, 'search-result')
            
            roles_list = search_result.find_elements(By.XPATH, "ul/li")
            print()
            print('Page %d --------------------' % (page_counter+1))
            for item in roles_list:
                role = Role(item, driver, apply=True)
                roles.append(role)
                print('Role %d: %s' % (len(roles), role.title))

            # go to next page
            try:
                search_result.find_element(By.XPATH, '//a[text()="Próximo"]').click()
                page_counter += 1
                time.sleep(1)
                # if page_counter > 4 : break # PAGE LIMIT
            except (NoSuchElementException, ElementNotInteractableException,
                    StaleElementReferenceException):
                break

    ### easy apply
    # load easy apply data
    easy_apply_cache_file = "easy_apply.csv"
    easy_apply_df = pd.read_csv(easy_apply_cache_file, delimiter=';')
    
    # iterate over easy_apply roles
    ea_roles = [role for role in roles if role.easy_apply]
    print()
    print('%d easy apply roles find, applying right now' % (len(ea_roles)))
    for role in ea_roles:
        try:
            print("Easy applying for: %s" % (role.title))

            # go to role url
            driver.get(role.link)

            # wait and click on "Enviar Candidatura Fácil"
            xpath = '//button[text()="Enviar Candidatura Fácil"] | //*[contains(text(), "Currículo já enviado")]' 
            el = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )

            # check if it was already applied
            if "Currículo já enviado" in el.get_attribute('innerText'):
                print('\talready applied')
                continue

            el.click()
            
            # wait for the modal with the questions
            xpath = '//h2[text()="Questionário da vaga"] | //*[contains(text(), "Currículo já enviado")] | //*[contains(text(), "Seu currículo foi enviado :)")]'

            el = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            
            if "Currículo já enviado" in el.get_attribute('innerText') or \
                "Seu currículo foi enviado :)" in el.get_attribute('innerText'):
                print('\tsuccessfully applied, no questions required')
                
            else:

                # read questions
                items = driver.find_elements(By.XPATH, '//div[@role="dialog"]/article/div/form/div')
                for item in items:
                    question = None

                    if item.find_elements(By.XPATH, "div/div/textarea"):
                        question = TextQuestion(item)

                    elif item.find_elements(By.XPATH, "div/div[@role='radiogroup']"):
                        question = RadioQuestion(item)

                    else:
                        raise Exception('Unknown type of question')

                    # check if the question already have a saved answer
                    matches = easy_apply_df[easy_apply_df['question'] == question.title]
                    if matches.shape[0]:
                        for _, row in matches.iterrows():
                            question.solve(row['answer'])

                    # if not ask the answer to the user
                    else:
                        user_input = None
                        print('User answer requested')
                        print('Press ENTER to skip')

                        # text input
                        if isinstance(question, TextQuestion):
                            print()
                            print(question.title)
                            print()
                            user_input = input("Please reply the question above:\n")

                        # radio input
                        elif isinstance(question, RadioQuestion):
                            print()
                            print(question.title)
                            print('\nOptions:')
                            for i, option in enumerate(question.options):
                                print("\t%d - %s" % (i, option))

                            while True:
                                user_input = input("Please select an option number:\n")
                                if user_input not in range(0, len(question.options)-1):
                                    print('invalid option')
                                else:
                                    break

                        question.solve(user_input)

                        # feed easy apply cache
                        easy_apply_df = easy_apply_df.append({
                            'question': question.title,
                            'answer': user_input
                        }, ignore_index=True)
                        easy_apply_df.to_csv(easy_apply_cache_file, sep=';', index=False)

                # click on submit
                driver.find_element(By.XPATH, '//button[text()="Enviar meu currículo"]').click()

                # check submition success
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "Currículo já enviado")]'))
                )
        
        except Exception as exc:
            role.applied_now = False
            role.apply_error = True
            role.error_message = str(exc)

        else:
            role.applied_now = True
            role.apply_error = False
            role.error_message = ""

    # create dataframe
    df = pd.DataFrame({
        "title": [role.title for role in roles],
        "link": [role.link for role in roles],
        "salary": [role.salary for role in roles],
        "location": [role.location for role in roles],
        "number_of_positions": [role.number_of_positions for role in roles],
        "date": [role.date for role in roles],
        "description": [role.description for role in roles],
        "application_date": [role.application_date for role in roles],
        "external": [role.external for role in roles],
        "compatible": [role.compatible for role in roles],
        "already_applied": [role.already_applied for role in roles],
        "applicable": [role.applicable for role in roles],
        "easy_apply": [role.easy_apply for role in roles],
        "applied_now": [role.applied_now for role in roles],
        "apply_error": [role.apply_error for role in roles],
        "error_message": [role.error_message for role in roles],
        "skipped": [role.skipped for role in roles],
    })

    # define types
    dtype = {
        "title": str,
        "link": str,
        "salary": str,
        "location": str,
        "number_of_positions": str,
        "date": str,
        "description": str,
        "application_date": str,
        "external": bool,
        "compatible": bool,
        "already_applied": bool,
        "applicable": bool,
        "easy_apply": bool,
        "applied_now": bool,
        "apply_error": bool,
        "error_message": str,
        "skipped": bool,
    }
    df = df.astype(dtype)

    # export dataframe
    df.to_excel('output.xlsx')
    print('Execution finished')

    # final report
    print()
    print()
    print('-'*50)
    print('Summary')
    print('-'*50)
    print('\t* %d roles have been read' % df.shape[0])
    print('\t* %d roles were already applied' % df[df['already_applied']].shape[0])
    print('\t* %d roles were external' % df[df['external']].shape[0])
    print('\t* %d roles were easy apply' % df[df['easy_apply']].shape[0])
    print('\t* %d applications done' % df[df['applied_now']].shape[0])
    print('\t* %d applications presented errors' % df[df['apply_error']].shape[0])

class Role:

    def __init__(self, item, driver, apply=False):
        """
        The constructor of the class can get the Selenium web element, parse all the data
        inside the HTML, check if it is possible to apply and then apply if the apply paramater
        is set to True.

        Parameters:
            - item: selenium web element already located
            - driver: selenium web driver (necessary to perform actions on the browser)
            - apply: apply for available roles
        """
        # make sure that all the attributes were initialized
        self.title = ""
        self.link = ""
        self.salary = ""
        self.external = False
        self.location = ""
        self.number_of_positions = ""
        self.date = ""
        self.compatible = False
        self.description = ""
        self.already_applied = False
        self.application_date = ""
        self.applicable = False
        self.easy_apply = False
        self.applied_now = False
        self.apply_error = False
        self.error_message = ""
        self.skipped = False

        # save html
        try:
            self.html = item.get_attribute('outerHTML')
        
            # check external
            self.external = "Vaga patrocinada" in self.html
            
            # get role title and link
            try:
                el = item.find_element(By.XPATH, 'article/article/header/div/div[1]/h2/a')
                self.title = el.get_attribute('innerHTML')
                self.link = el.get_attribute('href')
            except (NoSuchElementException, StaleElementReferenceException):
                self.title = NPTE
                self.link = NPTE

            # get salary
            try:
                el = item.find_element(By.XPATH, 'article/article/header/div/div[2]/div')
                self.salary = el.get_attribute('innerHTML')
            except NoSuchElementException:
                self.salary = NPTE

            # get location
            try:
                el = item.find_elements(By.XPATH, "article/article/header/div/div[2]/button/a")
                self.location = ', '.join([button.get_attribute('innerHTML') for button in el])
            except NoSuchElementException:
                self.location = NPTE

            # get amount of positions
            try:
                el = item.find_element(By.XPATH, "article/article/header/div/div[2]/strong")
                self.number_of_positions = el.get_attribute('innerHTML')
            except NoSuchElementException:
                self.number_of_positions = NPTE

            # get date
            try:
                el = item.find_element(By.XPATH, "article/article/header/div/div[2]/time/span")
                self.date = el.get_attribute('innerHTML')
            except NoSuchElementException:
                self.date = NPTE

            # get compatible
            self.compatible = "Alta compatibilidade com seu CV" in self.html

            # get description
            try:
                el = item.find_element(By.XPATH, 'article/article/div/div[1]/span')
                self.description = el.get_attribute("innerHTML")
            except (NoSuchElementException, StaleElementReferenceException):
                self.description = NPTE

            # already applied
            if "Candidatura Iniciada" in self.html:
                self.already_applied = True
                try:
                    el = item.find_element(By.XPATH, "article/article/div/div[2]/div/div/div/span")
                    self.application_date = re.findall(r'\d\d/\d\d/\d\d\d\d', el.get_attribute('innerHTML'))[0]
                except (NoSuchElementException, IndexError):
                    self.application_date = NPTE
            else:
                self.already_applied = False
                self.application_date = ""

            # it is possible to apply ?
            try:
                el = item.find_element(By.XPATH, 'article/article/div/div[2]/div/div/button')
                text = el.get_attribute('innerText')
                self.applicable = "Quero me candidatar" in text
                self.easy_apply = "Enviar Candidatura Fácil" in text
            except NoSuchElementException:
                self.applicable = False

            # apply
            if apply and self.applicable:

                # get apply button
                el = item.find_element(By.XPATH, 'article/article/div/div[2]/div/div/div/button')
                el.click()
                
                # wait modal
                el = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH,'//button[text()="Enviar meu currículo"]'))
                )
                el.click()
                
                # wait modal
                el = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, '//button[text()="Ok, entendi"]'))
                )
                el.click()
                self.applied_now = True

        except Exception as exc:
            self.applied_now = False
            self.apply_error = True
            self.error_message = str(exc)

        else:
            self.apply_error = False
            self.error_message = ""

class BaseQuestion:
    """
    This class defines the standard behavior of questions.
    """

    def __init__(self, item):
        """
        The constructor of the class can get the Selenium web element, parse all the data
        inside the HTML, parse the data to decide what kind of question it is and how to answer it.

        Parameters:
            - item: selenium web element already located
            - driver: selenium web driver (necessary to perform actions on the browser)
        """

        self.title = item.find_element(By.XPATH, 'div/strong').get_attribute('innerHTML')
        self.item = item

class RadioQuestion(BaseQuestion):

    def __init__(self, item):
        super().__init__(item)

        # get options
        els = item.find_elements(By.XPATH, "div/div/div[@role='radiogroup']/label/span[2]")
        self.options = [el.get_attribute('innerText').lower() for el in els]

    def solve(self, option:int):
        self.item.find_element(By.XPATH, "div/div/div[@role='radiogroup']/label[%d]/span[1]" % (option+1)).click()

class TextQuestion(BaseQuestion):

    def __init__(self, item):
        super().__init__(item)

    def solve(self, answer):
        el = self.item.find_element(By.XPATH, "div/div/textarea")
        el.send_keys(answer)

if __name__ == '__main__':
    bot()