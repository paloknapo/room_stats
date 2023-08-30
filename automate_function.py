from pydantic import BaseModel, ConfigDict
from stringcase import camelcase
from specklepy.api.client import SpeckleClient
from specklepy.transports.memory import MemoryTransport
from specklepy.transports.server import ServerTransport
from specklepy.api.operations import receive
from speckle_project_data import SpeckleProjectData
# to add pandas into the environment run this in terminal: poetry add pandas 
import pandas as pd

class FunctionInputs(BaseModel):
    """
    These are function author defined values, automate will make sure to supply them.
    """

    report_message: str

    class Config:
        alias_generator = camelcase


def automate_function(project_data:SpeckleProjectData, function_inputs:FunctionInputs, speckle_token:str):
    
    client = SpeckleClient(project_data.speckle_server_url)
    client.authenticate_with_token(speckle_token)
    commit = client.commit.get(project_data.project_id, project_data.version_id)
    branch = client.branch.get(project_data.project_id, project_data.model_id, 1)

    memory_transport = MemoryTransport()
    server_transport = ServerTransport(project_data.project_id, client)
    base = receive(commit.referencedObject, server_transport, memory_transport)

    # filter room data 

    elements = base['elements']

    table = {'Name':[], 'Area':[], 'Level':[]}

    # object types to look for
    types = ['Rooms']
    skip = True

    # get Rooms collection
    for el in elements:
        if el['name'] in types:
            skip = False
            for room in el['elements']:
                # check if level name is not null in case of unplaced rooms
                if room['level'] is not None:
                    table['Level'].append(room['level']['name'])
                    table['Name'].append(room['name'])
                    table['Area'].append(room['area'])
    
    if skip:
        print('This model has no ' + ', '.join(types).lower())
        return

    df = pd.DataFrame(table)

    print(round(df.groupby(['Level', 'Name'])['Area'].sum(), 2))

    print(function_inputs.report_message, round(df['Area'].sum(), 2), round(df['Area'].mean(),2), len(df))