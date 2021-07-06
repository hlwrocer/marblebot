def getRole(guild, name):
    for role in guild.roles:
        if name == str(role.name):
            return role
    return None
