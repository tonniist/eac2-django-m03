from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import Select


class SeleniumEAC2(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Administrador inicial para las pruebas
        User.objects.create_superuser(
            "isard", "isard@isardvdi.com", "pirineus"
        )

        options = Options()
        options.add_argument("-headless")

        cls.browser = webdriver.Firefox(options=options)
        cls.browser.implicitly_wait(8)

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super().tearDownClass()

    def test_grupos_y_permisos(self):
        b = self.browser
        url = self.live_server_url

        # 1. Entrar como administrador
        b.get(url + "/admin/")
        b.find_element(By.NAME, "username").send_keys("isard")
        b.find_element(By.NAME, "password").send_keys("pirineus")
        b.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()

        self.assertIn("Groups", b.page_source)
        print("OK - Login administrador")

        # 2. Crear los grupos basic y admin
        for nombre in ("basic", "admin"):
            b.get(url + "/admin/auth/group/add/")
            b.find_element(By.NAME, "name").send_keys(nombre)
            b.find_element(By.NAME, "_save").click()

        # 3. Verificar que basic no tiene permisos
        b.get(url + "/admin/auth/group/")
        b.find_element(By.LINK_TEXT, "basic").click()

        asignados = Select(b.find_element(By.ID, "id_permissions_to"))
        self.assertEqual(len(asignados.options), 0)
        print("OK - Grupo basic sin permisos")

        # 4. Asignar los 8 permisos al grupo admin
        b.get(url + "/admin/auth/group/")
        b.find_element(By.LINK_TEXT, "admin").click()

        opciones = b.find_elements(
            By.CSS_SELECTOR, "#id_permissions_from option"
        )

        permisos = [
            o.get_attribute("value")
            for o in opciones
            if " | user | " in o.text.lower()
            or " | group | " in o.text.lower()
        ]

        self.assertEqual(len(permisos), 8)

        selector = Select(b.find_element(By.ID, "id_permissions_from"))

        for permiso in permisos:
            selector.select_by_value(permiso)

        b.find_element(By.ID, "id_permissions_add").click()
        b.find_element(By.NAME, "_save").click()

        # 5. Comprobar que se han guardado
        b.get(url + "/admin/auth/group/")
        b.find_element(By.LINK_TEXT, "admin").click()

        asignados = Select(b.find_element(By.ID, "id_permissions_to"))
        self.assertEqual(len(asignados.options), 8)
        print("OK - Grupo admin con 8 permisos")

        # 6. Crear usuario boss mediante Selenium
        b.get(url + "/admin/auth/user/add/")

        b.find_element(By.NAME, "username").send_keys("boss")
        b.find_element(By.NAME, "password1").send_keys("BossEac2_2026!")
        b.find_element(By.NAME, "password2").send_keys("BossEac2_2026!")
        b.find_element(By.NAME, "_save").click()

        # 7. Configurar boss como staff
        b.get(url + "/admin/auth/user/")
        b.find_element(By.LINK_TEXT, "boss").click()

        staff = b.find_element(By.ID, "id_is_staff")
        if not staff.is_selected():
            staff.click()

        # Asignarle el grupo admin
        grupos = Select(b.find_element(By.ID, "id_groups_from"))
        grupos.select_by_visible_text("admin")
        b.find_element(By.ID, "id_groups_add").click()

        b.find_element(By.NAME, "_save").click()

        # 8. Verificar propiedades del usuario
        b.get(url + "/admin/auth/user/")
        b.find_element(By.LINK_TEXT, "boss").click()

        self.assertTrue(
            b.find_element(By.ID, "id_is_staff").is_selected()
        )

        self.assertFalse(
            b.find_element(By.ID, "id_is_superuser").is_selected()
        )

        grupos = Select(b.find_element(By.ID, "id_groups_to"))
        nombres = [o.text.strip() for o in grupos.options]
        self.assertIn("admin", nombres)

        print("OK - Usuario boss creado como staff y miembro de admin")

        # 9. Cerrar la sesion de isard
        b.delete_all_cookies()
        b.get(url + "/admin/")

        # 10. Iniciar sesion como boss
        b.find_element(By.NAME, "username").send_keys("boss")
        b.find_element(By.NAME, "password").send_keys("BossEac2_2026!")
        b.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()

        # 11. Comprobar acceso a Users y Groups
        b.find_element(By.LINK_TEXT, "Users")
        b.find_element(By.LINK_TEXT, "Groups")

        b.find_element(By.LINK_TEXT, "Users").click()
        self.assertIn("/admin/auth/user/", b.current_url)

        b.get(url + "/admin/")
        b.find_element(By.LINK_TEXT, "Groups").click()
        self.assertIn("/admin/auth/group/", b.current_url)

        print("OK - Boss puede acceder a Users y Groups")
        print("EAC2 - EJERCICIO PERSONALIZADO COMPLETADO")
