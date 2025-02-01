nmd = 5
groups = []
participants = [i for i in range(1, 22)]
# for i in range(0, nmd):
#     groups.append(participants[:4])
#     participants = participants[4:]
# if participants:
#     groups.append(participants)
for i in range(0, nmd - 1):
    groups.append(participants[: 4])
    participants = participants[4 :]
groups.append(participants[:2])
groups.append(participants[2:])
print(groups)