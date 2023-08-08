# built in imports
import time
import re

# dependency imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import pandas as pd

# local imports
from credentials import user, password
from urls import login, saved_search

# constants
NPTE = 'Not possible to extract'

def bot():
    driver = webdriver.Chrome()
    driver.maximize_window()

    try:

        # access catho login page
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

        # go to saved search link
        driver.get(saved_search)

        # page loop
        roles = []
        banner_closed = False
        page_counter = 0
        while True:

            # wait for search list
            search_result = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, 'search-result'))
            )
            time.sleep(3)

            # close banner
            if not banner_closed:
                try:
                    el = driver.find_element(By.XPATH, '//div[@class="container-close-app-banner"]')
                    el.click()
                except NoSuchElementException:
                    pass
                banner_closed = True

            # apply for the roles
            roles_list = search_result.find_elements(By.XPATH, "ul/li")
            print('Page %d: %d roles in this page' % (page_counter+1, len(roles_list)))
            for item in roles_list:
                role = Role(item, driver, apply=True)
                roles.append(role)
                print('Role %d: %s' % (len(roles), role.title))

            # go to next page
            try:
                search_result.find_element(By.XPATH, '//a[text()="Próximo"]').click()
                page_counter += 1
                time.sleep(1)
            except NoSuchElementException:
                break
        
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

    finally:
        driver.close()

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

        # save html
        self.html = item.get_attribute('outerHTML')
    
        # check external
        self.external = "Vaga patrocinada" in self.html
        
        # get role title and link
        try:
            el = item.find_element(By.XPATH, 'article/article/header/div/div[1]/h2/a')
            self.title = el.get_attribute('innerHTML')
            self.link = el.get_attribute('href')
        except NoSuchElementException:
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
        except NoSuchElementException:
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
            el = item.find_element(By.XPATH, 'article/article/div/div[2]/div/div/div/button')
            text = el.get_attribute('innerHTML')
            self.applicable = "Quero me candidatar" in text
            self.easy_apply = "Enviar Candidatura Fácil" in text
        except NoSuchElementException:
            self.applicable = False

        # apply
        if apply and self.applicable:

            try:
                # get apply button
                el = item.find_element(By.XPATH, 'article/article/div/div[2]/div/div/div/button')
                el.click()
                
                # wait modal
                el = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, '//button[text()="Enviar meu currículo"]'))
                )
                el.click()
                
                # wait modal
                el = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, '//button[text()="Ok, entendi"]'))
                )
                el.click()

                self.applied_now = True
                self.apply_error = False
                self.error_message = ""

            except Exception as exc:
                self.applied_now = False
                self.apply_error = True
                self.error_message = str(exc)

if __name__ == '__main__':
    bot()