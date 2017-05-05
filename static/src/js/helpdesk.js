openerp.web.ListView.List.include({

    htmlDecode: function(input){
        var e = document.createElement('div');
        e.innerHTML = input;
        return e.childNodes.length === 0 ? "" : e.childNodes[0].nodeValue;
        },
    
    render_cell: function (record, column) {
        var res = this._super(record, column);
        if (this.dataset.model == 'helpdesk.qa') {
            return this.htmlDecode(res);
            }
        return res;
        },
   
})

var cgtTabbedEditing = function(e){if (e.which == $.ui.keyCode.ENTER) {$(this).click();}};
var cgtTabbedFocus = function(){$(this).unbind('keypress', cgtTabbedEditing).bind('keypress',cgtTabbedEditing);};

$(document).ready(function(){
	setInterval(function() {
                $('.oe_list_content').find("tr:not(.oe_edition) td[tabindex=0]").unbind('focus', cgtTabbedFocus).bind('focus', cgtTabbedFocus);
        }, 800);
});

openerp.web.ListView.include({


    _next: function (next_record, options) {
            next_record = next_record || 'succ';
            var self = this;
            return this.save_edition().then(function (saveInfo) {
                if (!saveInfo) { return null; }
                if (saveInfo.created) {
                    return self.start_edition();
                }
                var record = self.records[next_record](
                        saveInfo.record, {wraparound: true});
		
		if(saveInfo.record.attributes.id == record.attributes.id) {
			return self.cancel_edition();
		}
		else {
	                return self.start_edition(record, options);
		}
            });
        },

    cancel_edition: function (force) {
            var self = this;
            return this.with_event('cancel', {
                editor: this.editor,
                form: this.editor.form,
                cancel: false
            }, function () {
                return this.editor.cancel(force).then(function (attrs) {
	            if(!attrs) {
		    	($(self.$el).find('button').focus());
		    }

                    if (attrs && attrs.id) {
                        var record = self.records.get(attrs.id);
                        if (!record) {
                            // Record removed by third party during edition
                            return;
                        }
                        return self.reload_record(record);
                    }
                    var to_delete = self.records.find(function (r) {
                        return !r.get('id');
                    });
                    if (to_delete) {
                        self.records.remove(to_delete);
                    }
                });
            });
        },

});

