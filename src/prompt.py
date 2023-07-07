from cmd2 import Cmd
import cmd2
from cmd2.table_creator import (
    AlternatingTable,
    BorderedTable,
    Column,
    HorizontalAlignment,
    SimpleTable,
)
from cmd2 import (
    Cmd2ArgumentParser,
    with_argparser
)

from mcp import *

class Control(Cmd):
    CATEGORY_INFO = "Puppets info"
    CATEGORY_ORDERS = "Puppets orders"
    CATEGORY_MISC = "Misc"

    def __init__(self, puppets, log=None):
        super().__init__()
        self.prompt = "$>"
        self.puppets = puppets
        
    def uuid_autocomplete(self):
        return list(self.puppets.keys()) 

    @cmd2.with_category(CATEGORY_INFO)
    def do_log(self, statement):
        self.poutput("LOG:")
    
    @cmd2.with_category(CATEGORY_INFO)
    def do_list(self, statement):
        puppets = self.puppets
        columns = [
                Column("UUID", width=8), 
                Column("IP Address", width=16),
                Column("Platform", width=48), 
                Column("Hostname", width=16)
            ]
        rows = list()
        for uuid in self.puppets:
            p = puppets[uuid]
            rows.append(
                [
                    uuid,
                    p["addr"][0],
                    p["platform"],
                    p["hostname"]
                ]
            )
        st = SimpleTable(columns)
        table = st.generate_table(rows)
        print(table)

    info_parser = Cmd2ArgumentParser()
    info_parser.add_argument("-u", "--uid", required=True, action="append", help="specify puppet", 
                                choices_provider=uuid_autocomplete)
    @cmd2.with_category(CATEGORY_INFO)
    @with_argparser(info_parser)
    def do_info(self, opts):
        for uuid in opts.uid:
            for key in self.puppets[uuid]:
                print(f"{key}: {self.puppets[uuid][key]}")

    execute_parser = Cmd2ArgumentParser()
    execute_parser.add_argument("-u", "--uid", required=False, action="append", help="specify puppet", 
                                choices_provider=uuid_autocomplete)
    execute_parser.add_argument("cmd", help="command to run on puppet")
    # execute given command to all or specified puppets uids
    @cmd2.with_category(CATEGORY_ORDERS)
    @with_argparser(execute_parser)
    def do_execute(self, opts):
        puppets = self.puppets
        uuids = opts.uid if opts.uid else puppets.keys()
        cmd = opts.cmd
        c = 0
        for uuid in uuids:
            puppets[uuid]["queue"].put(McpOrder("exec " + cmd))
            c += 1

        self.poutput(f"Running {cmd} against {c} puppets...")
