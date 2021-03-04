import pandas

from accounts.test.factories import GovDepartmentFactory, UserFactory
from accounts.models import GovDepartment, User
from supply_chains.test.factories import (
    StrategicActionFactory,
    StrategicActionUpdateFactory,
    SupplyChainFactory,
)
from supply_chains.models import (
    StrategicAction,
    StrategicActionUpdate,
    SupplyChain,
)

# 7 gov departments
# 5 supply chains per gov department (35 total)
# 5 strategic actions per supply chain (175 total)
# 10 updates per strategic action (1750)

for i in range(7):
    GovDepartmentFactory(name=f"Department {i+1}")

for dep in GovDepartment.objects.all():
    UserFactory(gov_department=dep)

for dep in GovDepartment.objects.all():
    SupplyChainFactory.create_batch(5, name="Fake supply chain", gov_department=dep)

for sc in SupplyChain.objects.all():
    StrategicActionFactory.create_batch(5, supply_chain=sc)

for sa in StrategicAction.objects.all():
    dep = sa.supply_chain.gov_department
    StrategicActionUpdateFactory.create_batch(
        10,
        strategic_action=sa,
        supply_chain=sa.supply_chain,
        user=User.objects.get(gov_department=dep),
    )
    # user needs to from the same gov department as the strat action


# To turn JSON to CSV with pandas

# files = ["users", "strategicActions", "strategicActionUpdates", "supplyChains", "govDepartments"]

# for file in files:
# df = pandas.read_json(f"{file}.json")
# csv = df.to_csv(f"{file}.csv", index=False)


# To make the CSVS
# csv = ResourceName.export().csv

# with open("filename.csv") as f:
#     f.write(csv)
