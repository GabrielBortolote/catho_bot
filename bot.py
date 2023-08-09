# built in imports
import time

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

    # instructions
    print('Instructions:')
    print('\t- %s -> read' % (emoji.emojize(':check_mark:')))
    print('\t- %s -> already applied' % (emoji.emojize(":check_mark_button:")))
    print('\t- %s -> applied right now' % (emoji.emojize(":pen:")))
    print('\t- %s -> error appling' % (emoji.emojize(':wrench:')))
    print('\t- %s -> external role' % (emoji.emojize(':globe_showing_Americas:')))
    print('\t- %s -> role suits perfect with your profile' % (emoji.emojize(':trophy:')))

    # search loop
    print("%d searches registered, starting execution" % len(searches))
    roles = []
    banner_closed = False

    try:
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

                # apply for the roles
                search_result = driver.find_element(By.ID, 'search-result')
                roles_list = search_result.find_elements(By.XPATH, "ul/li")
                print()
                print('Page %d --------------------' % (page_counter+1))
                for item in roles_list:
                    role = Role(item, driver, apply=False)
                    roles.append(role)

                    # set status icon
                    # standard icon
                    icon = emoji.emojize(':check_mark:')

                    # already applied icon
                    if role.already_applied:
                        icon = emoji.emojize(":check_mark_button:")
                    elif role.applied_now:
                        icon = emoji.emojize(":pen:")
                    elif role.apply_error:
                        icon = emoji.emojize(':wrench:')
                    elif role.external:
                        icon = emoji.emojize(':globe_showing_Americas:')

                    # additional icon
                    if role.compatible:
                        icon += emoji.emojize(':trophy:')


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
    finally:

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

if __name__ == '__main__':
    bot()