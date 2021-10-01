from locust import HttpUser, TaskSet, task, events, web
from GraphanaListener import GraphanaPlugin 
from kpi_listener import KpiPlugin

class FlightSearchTest(TaskSet):
    @task
    def open_login_page(self):
	    self.client.get("/login")

    @task
    def find_flight_between_Paris_and_Buenos_Aires(self):self.client.post("/reserve.php", {
            'fromPort': 'Paris', 'toPort': 'Buenos+Aires'
    })

    @task
    def purchase_flight_between_Paris_and_Buenos_Aires(self):self.client.post("/purchase.php", {
            'fromPort': 'Paris', 'toPort': 'Buenos+Aires',
            'airline': 'Virgin+America','flight': 43,
             'price': 472.56
    })

class MyLocust(HttpUser):
    tasks = [FlightSearchTest]
    host = "http://blazedemo.com"

    def __init__(self, environment):
        super().__init__(environment)        

    @events.init.add_listener
    def my_locust_init(environment, **_kwargs):
        KPI_SETTINGS = [{'/login': [('percentile_90', 5), ('rps', 500), ('error_rate', 0)]},
                        {'/reserve.php': [('percentile_90', 5), ('rps', 500), ('error_rate', 0)]},
                        {'/purchase.php': [('percentile_90', 5), ('rps', 500), ('error_rate', 0)]}]
        KpiPlugin(env=environment, kpis=KPI_SETTINGS)
    
    @events.init.add_listener
    def graphana_init(environment, **_kwargs):
        GraphanaPlugin(env=environment)

