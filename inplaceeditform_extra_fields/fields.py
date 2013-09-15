# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 by Pablo Martín <goinnn@gmail.com>
#
# This software is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.
import sys

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from inplaceeditform.commons import get_static_url
from inplaceeditform.fields import (AdaptorForeingKeyField,
                                    AdaptorCommaSeparatedManyToManyField,
                                    AdaptorImageField,
                                    AdaptorTextAreaField)

if sys.version_info.major == 2:
    string = basestring
else:
    string = str
    unicode = str


class AdaptorAutoCompleteProvider(object):

    def __init__(self, *args, **kwargs):
        super(AdaptorAutoCompleteProvider, self).__init__(*args, **kwargs)
        self.config['can_auto_save'] = 0

    def install_ajax_select(self):
        if 'ajax_select' in settings.INSTALLED_APPS:
            lookup = self.config.get('lookup', None)
            auto_field = self.auto_complete_field
            if lookup and auto_field:
                return True
        return False

    def get_field(self):
        field = super(AdaptorAutoCompleteProvider, self).get_field()
        if self.install_ajax_select():
            lookup = self.config.get('lookup', None)
            auto_field = self.auto_complete_field
            field.field = auto_field(lookup, required=field.field.required)
        return field

    def render_media_field(self,
                           template_name="inplaceeditform_extra_fields/adaptor_autocomplete/render_media_field.html",
                           extra_context=None):
        if self.install_ajax_select():
            extra_context = {'STATIC_URL_AJAX_SELECTS': get_static_url('ajax_selects')}
            return super(AdaptorAutoCompleteProvider, self).render_media_field(template_name, extra_context)
        return super(AdaptorAutoCompleteProvider, self).render_media_field()

    def render_value_edit(self):
        value = super(AdaptorAutoCompleteProvider, self).render_value_edit()
        if self.install_ajax_select():
            return render_to_string('inplaceeditform_extra_fields/adaptor_autocomplete/render_value_edit.html',
                                    {'value': value,
                                     'STATIC_URL': get_static_url(),
                                     'STATIC_URL_AJAX_SELECTS': get_static_url('ajax_selects'),
                                     'is_ajax': self.request.is_ajax()})
        return super(AdaptorAutoCompleteProvider, self).render_value_edit()


class AdaptorAutoCompleteForeingKeyField(AdaptorAutoCompleteProvider, AdaptorForeingKeyField):

    @property
    def auto_complete_field(self):
        try:
            from ajax_select.fields import AutoCompleteSelectField
            return AutoCompleteSelectField
        except ImportError:
            return None

    @property
    def name(self):
        return 'auto_fk'


class AdaptorAutoCompleteManyToManyField(AdaptorAutoCompleteProvider, AdaptorCommaSeparatedManyToManyField):

    @property
    def auto_complete_field(self):
        try:
            from ajax_select.fields import AutoCompleteSelectMultipleField
            return AutoCompleteSelectMultipleField
        except ImportError:
            return None

    @property
    def name(self):
        return 'auto_m2m'

    def get_value_editor(self, value):
        return [pk for pk in value.split("|") if pk]


class AdaptorImageThumbnailField(AdaptorImageField):

    # code of: http://dev.merengueproject.org/browser/trunk/merengueproj/merengue/uitools/fields.py?rev=5352#L59

    @property
    def name(self):
        return 'image_thumb'

    def install_sorl_thumbnail(self):
        if 'sorl.thumbnail' in settings.INSTALLED_APPS:
            try:
                from sorl import thumbnail
                return True
            except ImportError:
                pass
        return False

    def render_value(self,
                     field_name=None,
                     template_name='inplaceeditform_extra_fields/adaptor_image_thumb/render_value.html'):
        if self.install_sorl_thumbnail():
            return super(AdaptorImageThumbnailField, self).render_value(field_name=field_name, template_name=template_name)
        return super(AdaptorImageThumbnailField, self).render_value(field_name=field_name)


class AdaptorTinyMCEField(AdaptorTextAreaField):

    #code of: http://dev.merengueproject.org/browser/trunk/merengueproj/merengue/uitools/fields.py?rev=5352#L65

    @property
    def name(self):
        return 'tiny'

    @property
    def classes(self):
        return super(AdaptorTinyMCEField, self).classes + " textareainplaceedit"

    def __init__(self, *args, **kwargs):
        super(AdaptorTinyMCEField, self).__init__(*args, **kwargs)
        self.widget_options = self.config and self.config.get('widget_options', {})

    @property
    def TinyMCE(self):
        from inplaceeditform_extra_fields.widgets import TinyMCE
        return TinyMCE

    @classmethod
    def get_config(self, request, **kwargs):
        config = super(AdaptorTinyMCEField, self).get_config(request, **kwargs)
        if not request.is_ajax():
            config['fieldtypes'] = 'div.mce-content-body'
            config['focuswhenediting'] = "0"
            if not 'autosavetiny' in config:
                auto_save = config.get('autoSave', None) or config.get('autosave', None)
                if auto_save:
                    config['autosavetiny'] = str(int(auto_save))
                else:
                    config['autosavetiny'] = str(int(getattr(settings, 'INPLACEEDIT_AUTO_SAVE', False)))
            config['autosave'] = "0"
            config['autoSave'] = "0"
        return config

    def get_field(self):
        field = super(AdaptorTinyMCEField, self).get_field()
        extra_mce_settings = {}
        width = float(self.widget_options.get('width', '0').replace('px', ''))
        extra_mce_settings.update(getattr(settings, 'INPLACE_EXTRA_MCE', {}))
        field.field.widget = self.TinyMCE(extra_mce_settings=extra_mce_settings,
                                          config=self.config,
                                          width=width)
        return field

    def _render_value(self, field_name=None):
        return mark_safe(super(AdaptorTinyMCEField, self).render_value(field_name=field_name))

    def render_value(self, field_name=None):
        return self._render_value(field_name)

    def render_value_edit(self):
        value = self._render_value()
        if not value:
            value = self.empty_value()
        return render_to_string('inplaceeditform_extra_fields/adaptor_tiny/render_value_edit.html',
                                {'value': value,
                                 'adaptor': self,
                                 'field': self.get_field(),
                                 'is_ajax': self.request.is_ajax()})

    def render_field(self, template_name="inplaceeditform_extra_fields/adaptor_tiny/render_field.html", extra_context=None):
        return super(AdaptorTinyMCEField, self).render_field(template_name=template_name,
                                                             extra_context=extra_context)

    def render_media_field(self,
                           template_name="inplaceeditform_extra_fields/adaptor_tiny/render_media_field.html",
                           extra_context=None):
        extra_context = extra_context or {}
        context = {'STATIC_URL': get_static_url(subfix='inplaceeditform_extra_fields')}
        context.update(extra_context)
        return super(AdaptorTinyMCEField, self).render_media_field(template_name=template_name,
                                                                   extra_context=context)
