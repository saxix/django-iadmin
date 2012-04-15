import iadmin.api
__all__ = ['site1', 'site2']

site1 = iadmin.api.IAdminSite()
site2 = iadmin.api.IAdminSite('test', template_prefix='test')
