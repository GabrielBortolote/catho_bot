# built in imports
import time
from typing import List
from datetime import datetime

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
)
import emoji

# local imports
from credentials import user, password
from urls import login, searches
from Role import Role


def bot(apply:bool, output:str):
    """
    This function is the bot itself. Execute it to perform the automation.

    Parameters:
        - apply(bool): apply for the jobs if True, else just read them and prompt information
        - output(str): full path of the file name to save as report
    """

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

    # instructions
    print('Instructions:')
    print('\t- %s -> role suits perfect with your profile' % (emoji.emojize(':trophy:')))
    print('\t- %s -> applicable' % (emoji.emojize(":triangular_flag:")))
    print('\t- %s -> easy apply' % (emoji.emojize(":fast-forward_button:")))
    print('\t- %s -> has questions' % (emoji.emojize(":red_question_mark:")))
    print('\t- %s -> external role' % (emoji.emojize(':globe_showing_Americas:')))
    print('\t- %s -> already applied' % (emoji.emojize(":check_mark_button:")))
    print('\t- %s -> applied right now' % (emoji.emojize(":pen:")))
    print('\t- %s -> error appling' % (emoji.emojize(':cross_mark:')))

    # search loop
    print("\n\n%d searches registered, starting execution" % len(searches))
    roles = []
    banner_closed = False

    # read all the jobs
    for search_index, search in enumerate(searches):

        print('-'*50)
        print('Search number %d' % (search_index + 1))

        for _ in range(0,3):
            try:
                # go to search link
                driver.get(search)

                xpath = '//*[contains(text(), "Ops! Algo deu errado...")] | //*[@id="search-result"]'

                # wait for search list
                search_result = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )

                # something got wrong
                if search_result.get_attribute('id') != "search-result":
                    continue # try again

            except TimeoutException:
                pass # try again

            else:
                break # success

        # error loading search
        else:
            continue # go to next search

        # page loop
        page_counter = 0
        while True:

            # wait some time to load elements on the page
            time.sleep(5)

            # close banner
            if not banner_closed:
                try:
                    el = driver.find_element(By.XPATH, '//div[@class="container-close-app-banner"]')
                    el.click()
                except NoSuchElementException:
                    pass
                banner_closed = True

            # read all roles
            search_result = driver.find_element(By.ID, 'search-result')
            roles_list = search_result.find_elements(By.XPATH, "ul/li")
            print()
            print('Page %d --------------------' % (page_counter+1))
            for item in roles_list:
                role = Role(item)
                roles.append(role)

                # set status icon
                icon = ""

                if role.applicable:
                    icon += emoji.emojize(":triangular_flag:")

                if role.easy_apply:
                    icon += emoji.emojize(":fast-forward_button:")

                if role.questions:
                    icon += emoji.emojize(":red_question_mark:")
                    
                if role.external:
                    icon += emoji.emojize(':globe_showing_Americas:')

                if role.already_applied:
                    icon += emoji.emojize(":check_mark_button:")

                if role.applied_now:
                    icon += emoji.emojize(":pen:")

                if role.apply_error:
                    icon += emoji.emojize(':cross_mark:')


                if role.compatible:
                    icon += emoji.emojize(':trophy:')

                # prompt report
                print('Role %d: %s %s' % (len(roles), role.title, icon))

            # go to next page
            try:
                
                # if page_counter > 4 : break # PAGE LIMIT

                xpath = '//nav[@aria-label="pagination"]/a[contains(text(), "Próximo")]'
                WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                ).click()
                page_counter += 1
            except (TimeoutException, ElementNotInteractableException):
                break

    # apply for the jobs
    if apply:
        # default apply
        print()
        print('-'*50)
        print('Applying for default application jobs:')
        for role in [role for role in roles if role.default_apply]:
            role.apply(driver)

        # easy apply jobs
        print()
        print('-'*50)
        print('Applying for easy apply jobs (without questions):')
        for role in [role for role in roles if role.easy_apply and not role.questions]:
            role.apply(driver)

        print()
        print('-'*50)
        print('Applying for easy apply jobs (with questions):')
        for role in [role for role in roles if role.easy_apply and role.questions]:
            role.apply(driver)

    print()
    print('-'*50)
    print('Generationg report')
    generate_report(roles, output)

def generate_report(roles:List[Role], output:str):

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
        "applicable": [str(role.applicable) for role in roles],
        "unavailable": [str(role.unavailable) for role in roles],
        "external": [str(role.external) for role in roles],
        "compatible": [str(role.compatible) for role in roles],
        "already_applied": [str(role.already_applied) for role in roles],
        "default_apply": [str(role.default_apply) for role in roles],
        "easy_apply": [str(role.easy_apply) for role in roles],
        "questions": [str(role.questions) for role in roles],
        "applied_now": [str(role.applied_now) for role in roles],
        "apply_error": [str(role.apply_error) for role in roles],
        "error_message": [role.error_message for role in roles],
    })

    # export dataframe
    df.to_excel(output)
    print('Report saved at %s' % output)

    # final report
    print()
    print()
    print('-'*50)
    print('Summary')
    print('-'*50)
    print('\t* %d roles have been read' % len(roles))
    print('\t* %d roles were already applied' % len([r for r in roles if r.already_applied]))
    print('\t* %d roles were applicable, where:' % len([r for r in roles if r.applicable]))
    print('\t\t* %d roles were external' % len([r for r in roles if r.external]))
    print('\t\t* %d roles were default apply' % len([r for r in roles if r.default_apply]))
    print('\t\t* %d roles were easy apply, where:' % len([r for r in roles if r.easy_apply]))
    print('\t\t\t* %d roles have questions' % len([r for r in roles if r.questions]))
    print('\t\t\t* %d roles dont have questions' % len([r for r in roles if r.easy_apply and not r.questions]))
    print('\t* %d roles were unavailable' % len([r for r in roles if r.unavailable]))
    print('\t* %d applications done' % len([r for r in roles if r.applied_now]))
    print('\t* %d applications presented errors' % len([r for r in roles if r.apply_error]))

if __name__ == '__main__':
    output = 'output/'+datetime.now().strftime('%d-%m-%Y-%H-%M-%S.xlsx')
    bot(apply=True, output=output)