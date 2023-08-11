import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException
)

# constants
NPTE = 'Not possible to extract'

class Role:

    def __init__(self, item):
        """
        The constructor of the class can get the Selenium web element, parse all the data
        inside the HTML, check if it is possible to apply and then apply if the apply paramater
        is set to True.

        Parameters:
            - item: selenium web element already located
            - driver: selenium web driver (necessary to perform actions on the browser)
        """
        # make sure that all the attributes were initialized
        self.title = ""
        self.link = ""
        self.salary = ""
        self.external = False
        self.location = ""
        self.number_of_positions = ""
        self.date = ""
        self.applicable = False
        self.unavailable = False
        self.compatible = False
        self.description = ""
        self.already_applied = False
        self.application_date = ""
        self.default_apply = False
        self.easy_apply = False
        self.questions = False
        self.applied_now = False
        self.apply_error = False
        self.error_message = ""

        # save html
        self.html = item.get_attribute('outerHTML')
        
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

        # unavailable
        if "Candidatura indisponível" in self.html:
            self.applicable = False
            self.unavailable = True

        # already applied
        elif "Candidatura Iniciada" in self.html or "Currículo já enviado" in self.html:
            self.already_applied = True
            try:
                el = item.find_element(By.XPATH, "article/article/div/div[2]/div/div/div/span")
                self.application_date = re.findall(r'\d\d/\d\d/\d\d\d\d',
                                                    el.get_attribute('innerHTML'))[0]
            except (NoSuchElementException, IndexError):
                self.application_date = NPTE
        
        # possibly applicable
        else:
            self.already_applied = False
            self.application_date = ""

            # flags
            if 'Candidate-se no site da empresa' in self.html:
                self.external = True
                self.applicable = True

            elif 'Enviar Candidatura Fácil' in self.html:
                self.easy_apply = True
                self.applicable = True

                # does it have questions ?
                if 'Vaga com questionário' in self.html:
                    self.questions = True

            elif 'Quero me candidatar' in self.html:
                self.default_apply = True
                self.applicable = True

            else:
                self.applicable = False

    def apply(self, driver):
        """
        Apply to the job.

        Parameters:
            - driver: selenium web driver
        """
        print('\tapplying to: %s' % self.title)
        try:

            # default apply
            if self.default_apply:
                # go to role page
                driver.get(self.link)

                # wait for the button to be clickable
                xpath = '//button[text()="Quero me candidatar"]'
                el = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                el.click()

                # wait modal
                el = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH,'//button[text()="Enviar meu currículo"]'))
                )
                el.click()
                
                # wait modal
                xpath = '//button[text()="Ok, entendi"]'
                el = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
                el.click()
                self.applied_now = True

            # easy apply
            elif self.easy_apply:
                # go to role page
                driver.get(self.link)

                # wait for the button to be clickable
                xpath = '//button[text()="Enviar Candidatura Fácil"]'
                el = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                el.click()

                # the user have 10 minutes to reply the questions
                if self.questions:
                    print('waiting for user interaction')

                xpath = '//*[contains(text(), "Seu currículo foi enviado :)")]'
                try:
                    el = WebDriverWait(driver, 10*60).until(
                        EC.presence_of_element_located((By.XPATH, xpath))
                    )
                    self.applied_now = True
                
                # user did not interacted
                except TimeoutException:
                    print('\tException: user did not interacted')
                    self.applied_now = False
                    self.apply_error = True
                    self.error_message = "User did not interacted"

        except Exception as exc:
            self.applied_now = False
            self.apply_error = True
            self.error_message = str(exc)