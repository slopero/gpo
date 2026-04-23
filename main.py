from controllers.form_controller import FormController
from db.create_db import create_db
from db.params_model import ParamsModel
from views.main_window import MainWindow


def main():
	create_db()
	params_model = ParamsModel()
	form_controller = FormController(params_model)
	app = MainWindow(form_controller)
	app.run()


if __name__ == "__main__":
	main()
