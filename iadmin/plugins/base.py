

class IAdminPlugin(object):
    def __init__(self, adminsite):
        self.admin_site = adminsite
        self.name = adminsite.name

    @property
    def urls(self):
        return self.get_urls()