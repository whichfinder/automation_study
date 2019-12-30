# -*- coding: utf-8 -*-
import unittest
import os
import random
import time

from faker import Faker
from selenium import webdriver

from src.utils.db_postgress_helper import DbConnect
from src.pages.login_page import LoginPage
from src.pages.main_page import MainPage
from src.utils.api_helper import ApiHelper
from src.config_parser import Config
from src.utils.data_generator import generate_fake_data


class LoginTestSuite(unittest.TestCase):
    def setUp(self):
        self.url = Config.login_url
        self.driver = webdriver.Chrome()
        # self.driver.set_window_position(0, 0)
        # self.driver.set_window_size(1700, 1000)
        self.driver.get(self.url)

    def tearDown(self) -> None:
        self.driver.quit()

    def login(self, email=Config.api_login, password=Config.api_password):
        login_page = LoginPage(self.driver)
        login_page.specify_email(email)
        login_page.specify_pass(password)
        login_page.press_login()

    def test_login(self):
        main_page = MainPage(self.driver)
        self.login()
        self.assertTrue(main_page.wait_for_grid_render())

    def test_add_new_worker(self):
        main_page = MainPage(self.driver)
        db_conn = DbConnect()
        fake_data = generate_fake_data()
        email = fake_data["email"]
        sql_query = """select "email" from "worker" where email='{}';""".format(email)
        self.login()
        main_page.press_add_new_worker()
        main_page.enter_email_address(email)
        main_page.press_search_emails()
        main_page.enter_first_name(fake_data["first_name"])
        main_page.enter_last_name(fake_data["last_name"])
        main_page.press_create_button()
        self.assertTrue(main_page.wait_for_confirm_message())
        query_response = db_conn.fetch_one(sql_query)
        self.assertIsNotNone(query_response)

    def test_edit_personal_data_via_profile(self):
        db_conn = DbConnect()
        api_helper = ApiHelper()
        main_page = MainPage(self.driver)
        fake_data = generate_fake_data()
        fake_data2 = generate_fake_data()
        fake_email = fake_data["email"]
        new_email = fake_data2["email"]
        sql_query = """select "email" from "worker" where email='{}';""".format(new_email)
        body = {'email': fake_email,
                'firstname': fake_data["first_name"],
                'lastname': fake_data["last_name"]
                }
        api_helper.do_post_request("workers_creation", body)
        self.login()
        main_page.specify_search(fake_email)
        main_page.press_search_button()
        main_page.click_on_worker_name_in_grid()
        main_page.click_on_edit_profile()
        main_page.fill_fields_on_edit_pers_data(new_email,
                                                fake_data2["first_name"],
                                                fake_data2["last_name"])
        main_page.click_done_button()
        main_page.click_done_button()
        query_response = db_conn.fetch_one(sql_query)
        self.assertIsNotNone(query_response)

    def test_archived_worker(self):
        main_page = MainPage(self.driver)
        api_helper = ApiHelper()
        db_conn = DbConnect()
        fake_data = generate_fake_data()
        email = fake_data["email"]
        sql_query = """select "email" from worker where email='{}' and archived='true';""".format(email)
        # create worker
        body = {'email': email,
                'firstname': fake_data["first_name"],
                'lastname': fake_data["last_name"]
                }
        api_helper.do_post_request("workers_creation", body)
        self.login()
        main_page.specify_search(email)
        main_page.press_search_button()
        main_page.click_on_checkbox_next_to_worker()
        main_page.click_on_archive_button()
        main_page.click_on_archive_button_in_dialog()
        query_response = db_conn.fetch_one(sql_query)
        self.assertIsNotNone(query_response)

    def test_upload_file_via_profile(self):
        main_page = MainPage(self.driver)
        api_helper = ApiHelper()
        db_conn = DbConnect()
        fake_data = generate_fake_data()
        fake_data2 = generate_fake_data()
        image_path = os.path.join(os.path.abspath('..'), 'tmp', 'test.png')
        email = fake_data["email"]
        cert_name = fake_data["cert_name"]
        body = {'email': email,
                'firstname': fake_data["first_name"],
                'lastname': fake_data["last_name"]
                }
        sql_query = '''select "courseName" from "certificate" 
                where "workerId"=(select "id" from worker where email='{}') 
                and "courseName"='{}';'''.format(email, cert_name)
        api_helper.do_post_request("workers_creation", body)
        self.login()
        main_page.specify_search(email)
        main_page.press_search_button()
        main_page.click_on_worker_name_in_grid()
        main_page.click_add_new_record()
        main_page.send_file_to_upload_input(image_path)
        main_page.select_from_drop_down()
        main_page.type_certificate_name(cert_name)
        main_page.type_tr_provider_name(fake_data2["cert_name"])
        main_page.type_dates("2016-12-10", "2019-12-12")
        main_page.type_additional_info(fake_data2["cert_name"])
        main_page.press_submit_button()
        query_response = db_conn.fetch_one(sql_query)
        self.assertIsNotNone(query_response)

    def test_edit_certificates(self):
        main_page = MainPage(self.driver)
        api_helper = ApiHelper()
        db_conn = DbConnect()
        fake_data = generate_fake_data()
        fake_data2 = generate_fake_data()
        email = fake_data["email"]
        first_name = fake_data["first_name"]
        last_name = fake_data["last_name"]
        image_file = "efb9c5a7-862b-46ca-9ce3-7c8110d0cbff_share rules.png"
        query = """select "id" from worker where email='{}';""".format(email)
        # create worker
        worker_body = {'email': email, 'firstname': first_name, 'lastname': last_name}
        api_helper.do_post_request('workers_creation', worker_body)
        # get id for this worker
        worker_id = db_conn.fetch_one(query)[0]
        # add certificate to this worker
        cert_body = {'courseName': fake_data["cert_name"],
                     'description': fake_data["random_phrase"],
                     'expiration': "2030-11-05T16:01:38.433Z",
                     'file': image_file,
                     'issued': "2016-11-05T16:01:38.433Z",
                     'trainingProvider': fake_data2["cert_name"],
                     'workerId': worker_id
                     }
        certificate_query = """select "courseName" from "certificate" where "workerId"=(
        select "id" from worker where email='{}') 
        and "courseName"='{}' 
        and "description"='{}' 
        and "trainingProvider"='{}' 
        and "file"='{}';""".format(email, "Certificate name after EDITING",
                                   "Additional Certificate Details after EDITING",
                                   "Training Provider Name after EDITING", image_file)
        api_helper.do_post_request('certificates_creation', cert_body)
        # edit certificate via UI
        self.login()
        main_page.specify_search(email)
        main_page.press_search_button()
        main_page.click_on_worker_name_in_grid()
        main_page.click_edit_certificates_control()
        main_page.type_certificate_name("Certificate name after EDITING")
        main_page.type_tr_provider_name("Training Provider Name after EDITING")
        main_page.type_dates("2000-01-01", "2040-12-12")
        main_page.type_additional_info("Additional Certificate Details after EDITING")
        main_page.press_submit_button()
        query_response = db_conn.fetch_one(certificate_query)
        self.assertIsNotNone(query_response)

    def test_save_teams(self):
        db_conn = DbConnect()
        main_page = MainPage(self.driver)
        fake_data = generate_fake_data()
        team_name = fake_data["cert_name"]
        sql_query = '''select "name" from "team" where name='{}';'''.format(team_name)
        self.login()
        main_page.click_on_checkbox_next_to_worker(1)
        main_page.click_on_checkbox_next_to_worker(2)
        main_page.click_on_checkbox_next_to_worker(3)
        main_page.click_on_checkbox_next_to_worker(4)
        main_page.click_on_checkbox_next_to_worker(5)
        main_page.click_save_team_button()
        main_page.type_team_name_while_saving(team_name)
        main_page.click_save_button_while_saving_team()
        main_page.click_done_button()
        query_response = db_conn.fetch_one(sql_query)
        self.assertIsNotNone(query_response)

    def test_verify_project_team_filter(self):
        main_page = MainPage(self.driver)
        api_helper = ApiHelper()
        db_conn = DbConnect()
        fake_data = generate_fake_data()
        team_name = fake_data["cert_name"]
        sql_query = '''select "id" from "worker" where "employerId" = '{}';'''.format(Config.db_login)
        query_response = db_conn.fetch_all(sql_query)
        worker_id = random.choice(query_response)[0]
        body = {
            'name': team_name,
            'workerIds': [worker_id]
        }
        api_helper.do_post_request("teams_creation", body)
        self.login()
        main_page.open_project_teams_filter()
        main_page.mark_checkbox_in_modals()
        main_page.click_apply_button_in_modals()
        self.assertTrue(main_page.verify_chips_is_present())
        main_page.select_all_workers_in_the_grid()
        self.assertTrue(main_page.verify_text_of_counting_worker())

    def test_share_workers_to_another_employee(self):
        fake = Faker()
        main_page = MainPage(self.driver)
        api_helper = ApiHelper()
        db_conn = DbConnect()
        fake_data = generate_fake_data()
        fake_data2 = generate_fake_data()
        recipient_name = fake_data["cert_name"]
        recipient_email = Config.api_second_login
        recipient_company_name = fake_data2["random_phrase"]
        project_name = fake_data2["cert_name"]
        comments = fake_data["random_phrase"]
        for i in range(5):
            body = {'email': fake.email(),
                    'firstname': fake.first_name(),
                    'lastname': fake.last_name()
                    }
            api_helper.do_post_request("workers_creation", body)
        self.login()
        main_page.click_on_checkbox_next_to_worker(1)
        main_page.click_on_checkbox_next_to_worker(2)
        main_page.click_on_checkbox_next_to_worker(3)
        main_page.click_on_checkbox_next_to_worker(4)
        main_page.click_on_checkbox_next_to_worker(5)
        main_page.click_share_team_button()
        main_page.fill_recipient_name_while_sharing(recipient_name)
        main_page.fill_recipient_email_while_sharing(recipient_email)
        main_page.fill_recipient_company_name_while_sharing(recipient_company_name)
        main_page.fill_project_name_while_sharing(project_name)
        main_page.fill_comments_for_recipient_while_sharing(comments)
        main_page.click_share_button_while_sharing()
        main_page.click_done_button()
        main_page.click_sign_out()
        self.login(Config.api_second_login)
        self.assertTrue(main_page.wait_for_grid_render())




