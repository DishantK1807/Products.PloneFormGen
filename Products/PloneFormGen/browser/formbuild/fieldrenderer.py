import sys, traceback

from zope import component, interface
from Acquisition import aq_inner, aq_parent, aq_base

from plone.memoize.view import memoize

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.Five.browser import BrowserView
from Products.CMFCore.utils import getToolByName
from Products.Archetypes.Field import Field as BaseField

from Products.PloneFormGen.interfaces import IPloneFormGenForm
from Products.PloneFormGen.browser.formbuild.interfaces import IPFGFieldRenderer

class FieldRenderer(BrowserView):
    """Render a field base on the request.
    """
    template = ViewPageTemplateFile('fieldrenderer.pt')
    interface.implements(IPFGFieldRenderer)

    def __init__(self, context, request):
        BrowserView.__init__(self, context, request)
        self.fgform = aq_parent(aq_inner(self.context))
        while self.fgform and not IPloneFormGenForm.providedBy(self.fgform):
            self.fgform = aq_parent(aq_inner(self.fgform))
        formpath = ":".join(self.fgform.getPhysicalPath())
        #Relative path from the form object
        self.rel_path = ":".join(context.getPhysicalPath())[len(formpath)+1:]
        #Field's view mode, default = edit
        self.mode = request.form.get('mode', 'edit')
        #Field's render mode, default = edit (embed field's edit view)
        if self.mode == 'view':
            #If mode = view: We are not even in form view, but in form's data view.
            #rendermode are meaningless
            self.rendermode = ''
        else:
            self.rendermode = request.form.get('rendermode', 'edit')
        self.field = context
        self.fieldname = context.getId()
        self.isATField = isinstance(aq_base(self.context).fgField,BaseField) 
        #TODO: How should we pass errors for the view when render :((
        self.errors = {} #request.form.get('errors', {})

    def value(self):
        """Return field's value, just have meaning when we're in view mode
        """
        #TODO: Make this work with file field
        if self.mode != 'view':
            return None
        return self.request.form.get('value', '')

    def __call__(self):
        #TODO: Better exception handle needed ? atm just raise all of them out
        if self.fgform is None:
            raise("Unable to locate form object from the request.")
        if self.mode == 'view' and self.value is None:
            raise("In order to render the field in view mode, \
                   you need to provide the field's value.")
        return self.template()

    @property
    @memoize
    def atfields(self):
        result = []
        if not self.isATField:
            return result
        schematas = self.context.Schemata()
        interested_fieldsets = ['default']
        for fieldset in interested_fieldsets:
            result.extend(schematas[fieldset].editableFields(self.context, visible_only=True))
        return result

    def helperjs(self):
        """Return list of helper js-es those are needed to render the field
        """
        result = set(self.context.getUniqueWidgetAttr(self.atfields, 'helper_js'))
        result.update(self.fgform.getUniqueWidgetAttr([self.context.fgField] , 'helper_js'))
        return result


    def helpercss(self):
        """Return list of helper css-es those are needed to render the field
        """
        result = set(self.context.getUniqueWidgetAttr(self.atfields, 'helper_css'))
        result.update(self.fgform.getUniqueWidgetAttr([self.context.fgField] , 'helper_css'))
        return result
