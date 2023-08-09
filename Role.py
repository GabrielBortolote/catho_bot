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
            if "Candidatura Iniciada" in self.html or "Currículo já enviado" in self.html:
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
                    el = item.find_element(By.CSS_SELECTOR, 'button[title^="Quero me"]')
                    text = el.get_attribute('innerText')
                    self.applicable = "Quero me candidatar" in text
                    self.easy_apply = "Enviar Candidatura Fácil" in text
                except NoSuchElementException:
                    self.applicable = False

            # apply
            if apply and self.applicable:

                # get apply button
                el = item.find_element(By.CSS_SELECTOR, 'button[title^="Quero me"]')
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

            # easy apply
            elif apply and self.easy_apply:

                # get apply button
                el = item.find_element(By.CSS_SELECTOR, 'button[title^="Quero me"]')
                el.click()

                # the user have 10 minutes to reply the questions
                print('\twaiting user interaction')
                xpath = '//*[contains(text(), "Seu currículo foi enviado :)")]'
                try:
                    el = WebDriverWait(driver, 600).until(
                        EC.presence_of_element_located((By.XPATH, xpath))
                    )
                    print('\tuser interaction finished, keep going')
                    self.applied_now = True
                
                except TimeoutException:
                    # close modal
                    driver.find_element(By.XPATH, '//button[@aria-label="close dialog"]').click()
                    print('\tuser did not interacted')
                    self.applied_now = False
                    self.apply_error = True
                    self.error_message = "User did not interacted"


        except Exception as exc:
            self.applied_now = False
            self.apply_error = True
            self.error_message = str(exc)