odoo.define('flexipharmacy.chrome', function (require) {
"use strict";

	var chrome = require('point_of_sale.chrome');
	var gui = require('point_of_sale.gui');
	var PosBaseWidget = require('point_of_sale.BaseWidget');
	var core = require('web.core');
	var rpc = require('web.rpc');
	var ActionManager = require('web.ActionManager');
	var models = require('point_of_sale.models');
	var session = require('web.session');
	var bus_service = require('bus.BusService');
	var bus = require('bus.Longpolling');
	var cross_tab = require('bus.CrossTab').prototype;

	var _t = core._t;
	var QWeb = core.qweb;

	function start_lock_timer(time_interval,self){
        var $area = $(document),
        idleActions = [{
            milliseconds: time_interval * 100000,
            action: function () {
            	var params = {
    	    		model: 'pos.session',
    	    		method: 'write',
    	    		args: [self.pos.pos_session.id,{'is_lock_screen' : true}],
    	    	}
    	    	rpc.query(params, {async: false}).then(function(result){}).fail(function(){
                	self.pos.db.notification('danger',"Connection lost");
                });
                // $('.lock_button').css('background-color', 'rgb(233, 88, 95)');
                $('.freeze_screen').addClass("active_state");
                $(".unlock_button").fadeIn(2000);
                $('.unlock_button').show();
                $('.unlock_button').css('z-index',10000);
            }
        }];
        function lock (event, times, undefined) {
            var idleTimer = $area.data('idleTimer');
            if (times === undefined) times = 0;
            if (idleTimer) {
                clearTimeout($area.data('idleTimer'));
            }
            if (times < idleActions.length) {
                $area.data('idleTimer', setTimeout(function () {
                    idleActions[times].action();
                    lock(null, ++times);
                }, idleActions[times].milliseconds));
            } else {
                $area.off('mousemove click', lock);
            }
        };
        $area
            .data('idle', null)
            .on('mousemove click', lock);
        lock();
    }

	chrome.Chrome.include({
		events: {
            "click #product_sync": "product_sync",
            "click #pos_lock": "pos_lock",
			"click #messages_button": "messages_button",
			"click #close_draggable_panal": "close_draggable_panal",
			"click #delete_msg_history": "delete_msg_history",
			"click #delivery_list_chrome": "delivery_list_chrome",
			"click #close_draggable_panal_delivery_order" :"close_draggable_panal_delivery_order",
        },
        delivery_list_chrome: function(){
        	var self = this;
			if($('#draggablePanelList_delivery_order').css('display') == 'none'){
				$('#draggablePanelList_delivery_order').animate({
    	            height: 'toggle'
    	            }, 200, function() {
    	        });
				var delivery_orders = _.filter(self.pos.get('pos_order_list'), function(item) {
				     return item.delivery_type == 'pending'
				});
				self.render_delivery_order_list(delivery_orders);
				$('#head_data_delivery_orders').text(_t("Delivery Orders"));
			} else{
				$('#draggablePanelList_delivery_order').animate({
    	            height: 'toggle'
    	            }, 200, function() {
    	        });
			}
        },
        close_draggable_panal_delivery_order: function(){
        	$('#draggablePanelList_delivery_order').animate({
	            height: 'toggle'
	            }, 200, function() {
	        });
        },
        product_sync: function(){
        	var self = this;
        	self.pos.load_new_products();
        	$('.prodcut_sync').toggleClass('rotate', 'rotate-reset');
		},
		build_widgets: function(){
			var self = this;
			this._super();
			/*if(!self.pos.load_background){
				self.$el.find('#product_sync').trigger('click');
			}*/
			if(!self.pos.is_rfid_login){
        		$('.page-container').css({
        			'width':'100%',
        		});
        	}
			self.slider_widget = new SliderWidget(this);
			self.pos_cart_widget = new PosCartCountWidget(this);
        	self.slider_widget.replace(this.$('.placeholder-SliderWidget'));
        	self.pos_cart_widget.replace(this.$('.placeholder-PosCartCountWidget'));
			self.gui.set_startup_screen('login');
			self.gui.show_screen('login');
			this.call('bus_service', 'updateOption','lock.data',session.uid);
            cross_tab._isRegistered = true;
            cross_tab._isMasterTab = true;
			this.call('bus_service', 'startPolling');
		    this.call('bus_service', 'onNotification', self, self._onNotification);
			this.call('bus_service', '_poll');
		},
		save_receipt_for_reprint:function(){
            var self = this;
            var order = this.pos.get_order();
			var save_paymentlines = order.get_paymentlines();
			var receipt_data = order.export_for_printing() 
			var env = {
                widget:self,
                pos: this.pos,
                order: order,
                receipt: order.export_for_printing(),
                orderlines: order.get_orderlines(),
                paymentlines: order.get_paymentlines(),
            };
            var receipt_html = QWeb.render('PosTicket',env);
        	order.set_pos_normal_receipt_html(receipt_html.replace(/<img[^>]*>/g,"").replace(/<object[^>]*>/g,""));
        	var receipt = QWeb.render('XmlReceipt',env);
        	order.set_pos_xml_receipt_html(receipt.replace(/<img[^>]*>/g,"").replace(/<object[^>]*>/g,""));
			console.log('DATA TO SAVE ****************');
			console.log(env);
			console.log(save_paymentlines);
			console.log(receipt_data);
			console.log(receipt_data.paymentlines);
			console.log(receipt_data['paymentlines']);
			console.log(receipt_data['tax_details']);
			var payment_lines = []
			Object.keys(save_paymentlines).forEach(key => {
				console.log('DATA', save_paymentlines[key])
				var new_payment = {"name": save_paymentlines[key].name, "amount": save_paymentlines[key].amount.toFixed(2)}
				payment_lines.push(new_payment);
			});
			var final_payment_data = {"paymentlines": payment_lines}
			console.log('DATA FINAL', final_payment_data);

			var tax_lines = []
			var tax_details = receipt_data['tax_details']
			Object.keys(tax_details).forEach(key => {
				console.log('DATA', tax_details[key])
				var new_tax = {"name": tax_details[key].name, "amount": tax_details[key].amount.toFixed(2)}
				tax_lines.push(new_tax);
			});
			//var payment_lines_html = QWeb.render('XmlPaymentLines', final_payment_data);
			//console.log('DATA FINAL HTML', payment_lines_html);
			//console.log(payment_lines_html);
			//var taxes_lines_html = QWeb.render('XmlTaxLines',receipt_data.tax_details);
			var final_tax_data = {"tax_lines": tax_lines}
			console.log('Taxes', JSON.stringify(final_tax_data))
			order.set_pos_xml_receipt_payment_lines(JSON.stringify(final_payment_data));
			order.set_pos_xml_receipt_taxes_lines(JSON.stringify(final_tax_data));
			
        },
		_onNotification: function(notifications){
			var self = this;
			for (var notif of notifications) {
	    		if(notif[1] && notif[1].terminal_lock){
					if(notif[1].terminal_lock[0]){
						if(self.pos.pos_session && (notif[1].terminal_lock[0].session_id[0] == self.pos.pos_session.id)){
							self.pos.set_lock_status(notif[1].terminal_lock[0].lock_status);
							self.pos.set_lock_data(notif[1].terminal_lock[0]);
						}
					}
	    		} else if(notif[1] && notif[1].terminal_message){
	    			if(notif[1].terminal_message[0]){
            			if(self.pos.pos_session.id == notif[1].terminal_message[0].message_session_id[0]){
            				var message_index = _.findIndex(self.pos.message_list, function (message) {
            					return message.id === notif[1].terminal_message[0].id;
                            });
                			if(message_index == -1){
                				self.pos.message_list.push(notif[1].terminal_message[0]);
                				self.render_message_list(self.message_list);
                				$('#message_icon').css("color", "#5EB937");
                				self.pos.db.notification('info',notif[1].terminal_message[0].sender_user[1]+' has sent new message.');
                			}
            			}
            		}
	    		}
	    		else if(notif[1] && notif[1].rating){
                    var order = self.pos.get_order();
                    if(order){
                        order.set_rating(notif[1].rating);
                    }
                } else if(notif[1] && notif[1].partner_id){
                	var partner_id = notif[1].partner_id;
                	var partner = self.pos.db.get_partner_by_id(partner_id);
                    var order = self.pos.get_order();
                    if(partner){
                        if(order){
                            order.set_client(partner);
                        }
                    }else{
                        if(partner_id){
//                            var fields = _.find(self.pos.models,function(model){ return model.model === 'res.partner'; }).fields;
                            var params = {
                                model: 'res.partner',
                                method: 'search_read',
//                                fields: fields,
                                domain: [['id','=',partner_id]],
                            }
                            rpc.query(params, {async: false})
                            .then(function(partner){
                                if(partner && partner.length > 0){
                                	self.pos.db.add_partners(partner);
                                	order.set_client(partner[0]);
                                }else{
                                	self.pos.db.notification('danger',"Patient not loaded in POS.");
                                }
                            });
                        }
                    }
                } else if(notif[1] && notif[1].delivery_pos_order){
                	var existing_orders = self.pos.get('pos_order_list');
                	var filtered = _.filter(existing_orders, function(item) {
                	    return item.id !== notif[1].delivery_pos_order[0].id
                	});
                	filtered.push(notif[1].delivery_pos_order[0]);
                	filtered = _.sortBy(filtered, 'id').reverse();
                	self.pos.db.add_orders(filtered);
					self.pos.set({'pos_order_list':filtered});
					var delivery_orders = _.filter(self.pos.get('pos_order_list'), function(item) {
					     return item.delivery_type == 'pending'
					});
					self.render_delivery_order_list(delivery_orders);
                }
	    	}
		},
		render_delivery_order_list: function(orders){
        	var self = this;
        	if(orders){
        		var contents = $('.message-panel-body2');
	            contents.html("");
	            var order_count = 0;
	            for(var i = 0, len = Math.min(orders.length,1000); i < len; i++){
	                var order = orders[i];
                	order_count ++;
	                var orderlines = [];
	                order.amount_total = parseFloat(order.amount_total).toFixed(2);
	            	var clientline_html = QWeb.render('DeliveryOrdersQuickWidgetLine',{widget: this, order:order, orderlines:orderlines});
	                var clientline = document.createElement('tbody');
	                clientline.innerHTML = clientline_html;
	                clientline = clientline.childNodes[1];
	                contents.append(clientline);
	            }
	            self.pos.delivery_order_count = order_count
//            	$('.notification-count').show();
            	$('.delivery_order_count').text(order_count);
        	}
        },
		pos_lock: function(){
			var self = this;
			self.pos.session_by_id = {};
			var domain = [['state','=', 'opened'],['id','!=',self.pos.pos_session.id]];
         	var params = {
	    		model: 'pos.session',
	    		method: 'search_read',
	    		domain: domain,
	    	}
	    	rpc.query(params, {async: false}).then(function(sessions){
	    		if(sessions && sessions.length > 0){
	    			_.each(sessions,function(session){
	    				self.pos.session_by_id[session.id] = session;
	    			});
	    			self.pos.gui.show_popup('terminal_list',{'sessions':sessions});
	    		} else{
	    			self.pos.db.notification('danger',_t('Active sessions not found!'));
	    		}
	    	}).fail(function(){
            	self.pos.db.notification('danger',"Connection lost");
            });
		},
		messages_button: function(){
			var self = this;
			if($('#draggablePanelList').css('display') == 'none'){
				$('#draggablePanelList').animate({
    	            height: 'toggle'
    	            }, 200, function() {
    	        });
				self.render_message_list(self.pos.message_list);
				$('.panel-body').css({'height':'auto','max-height':'242px','min-height':'45px','overflow':'auto'});
				$('.head_data').html(_t("Message"));
				$('.panel-body').html("Message-Box Empty");
			}else{
				$('#draggablePanelList').animate({
    	            height: 'toggle'
    	            }, 200, function() {
    	        });
			}
		},
		close_draggable_panal:function(){
			$('#draggablePanelList').animate({
	            height: 'toggle'
	            }, 200, function() {
	        });
		},
		delete_msg_history: function(){
			var self = this;
			var params = {
	    		model: 'message.terminal',
	    		method: 'delete_user_message',
	    		args: [self.pos.pos_session.id],
	    	}
	    	rpc.query(params, {async: false}).then(function(result){
	    		if(result){
	    			self.pos.message_list = []
		    		self.render_message_list(self.pos.message_list)
	    		}
	    	}).fail(function(){
            	self.pos.db.notification('danger',"Connection lost");
            });
		},
		render_message_list: function(message_list){
	    	var self = this;
	        if(message_list && message_list[0]){
	        	var contents = $('.message-panel-body');
		        contents.html("");
		        var temp_str = "";
		        for(var i=0;i<message_list.length;i++){
		            var message = message_list[i];
	                var messageline_html = QWeb.render('MessageLine',{widget: this, message:message_list[i]});
		            temp_str += messageline_html;
		        }
		        contents.html(temp_str)
		        $('.message-panel-body').scrollTop($('.message-panel-body')[0].scrollHeight);
		        $('#message_icon').css("color", "gray");
	        } else{
	        	var contents = $('.message-panel-body');
		        contents.html("");
	        }
	    },
	    user_icon_url(id){
			return '/web/image?model=res.users&id='+id+'&field=image_small';
		},
	});

    var SliderWidget = PosBaseWidget.extend({
        template: 'SliderWidget',
        init: function(parent, options){
            var self = this;
            this._super(parent,options);
            self.click_username = function(){
				self.pos.get_order().destroy();
				self.gui.show_screen('login');
//                self.gui.select_user({
//                    'security':     true,
//                    'current_user': self.pos.get_cashier(),
//                    'title':      _t('Change Cashier'),
//                }).then(function(user){
//                    self.pos.set_cashier(user);
//                    self.renderElement();
//                });
            };
            self.sidebar_button_click = function(){
            	if(self.gui.get_current_screen() !== "receipt"){
            		$(this).parent().removeClass('oe_hidden');
                	$(this).parent().toggleClass("toggled");
                	$(this).find('i').toggleClass('fa fa-chevron-right fa fa-chevron-left');
            	}
        	};
        	self.open_product_screen = function(){
                self.gui.show_screen('product-screen');
                self.close_sidebar();
        	};
        	self.open_expiry_deshboard = function(){
        		self.gui.show_screen('product_expiry_deshboard');
        		self.close_sidebar();
        	},
        	self.open_sales_deshboard = function(){
        		self.gui.show_screen('pos_dashboard_graph_view');
        		self.close_sidebar();
        	},
        	self.out_of_stock_detail = function(){
                self.gui.show_screen('product_out_of_stock_screen');
        		self.close_sidebar();
        	},
        	self.user_change_pin = function(){
                self.gui.show_popup('change_user_pin_popup');
                self.close_sidebar();
        	},
        	self.internal_stock_transfer = function(){
                var selectedOrder = self.pos.get_order();
                var currentOrderLines = selectedOrder.get_orderlines();
                if(self.pos.stock_pick_typ.length == 0){
                    return alert(_t("You can not proceed with 'Manage only 1 Warehouse with only 1 stock location' from inventory configuration."));
                }
                if(currentOrderLines.length == 0){
                    return alert(_t("You can not proceed with empty cart."));
                }
                self.close_sidebar();
                self.gui.show_popup('int_trans_popup',{'stock_pick_types':self.pos.stock_pick_typ,'location':self.pos.location_ids});
        	};
        	self.gift_card_screen = function(){
        		self.close_sidebar();
        		self.gui.show_screen('giftcardlistscreen');
        	};
        	/*self.delivery_details_screen = function(){
        		self.gui.show_screen('delivery_details_screen');
        		self.close_sidebar();
        	},*/
        	self.discard_product_screen = function(){
        		self.close_sidebar();
        		self.gui.show_screen('stockpickinglistscreen');
        	},
        	self.gift_voucher_screen = function(){
        		self.close_sidebar();
        		self.gui.show_screen('voucherlistscreen');
        	};
        	self.open_order_screen = function(){
        		self.gui.show_screen('orderlist');
        		self.close_sidebar();
        	};
        	self.recurrent_order_screen = function(){
        		self.gui.show_screen('recurrent_order_screen');
        		self.close_sidebar();
        	};
        	self.all_sale_orders = function(){
        	    self.gui.show_screen('saleorderlist');
        		self.close_sidebar();
        	};
        	self.sale_invoice = function(){
        	    self.gui.show_screen('invoice_list');
        		self.close_sidebar();
        	};
        	self.print_lastorder = function(){
        		self.close_sidebar();
        		if(self.pos.get('pos_order_list').length > 0){
					var last_order_id = Math.max.apply(Math,self.pos.get('pos_order_list').map(function(o){return o.id;}))
					var result = self.pos.db.get_order_by_id(last_order_id);
	                var selectedOrder = self.pos.get_order();
	                var currentOrderLines = selectedOrder.get_orderlines();
	                if(currentOrderLines.length > 0) {
	                	selectedOrder.set_order_id('');
	                    for (var i=0; i <= currentOrderLines.length + 1; i++) {
	                    	_.each(currentOrderLines,function(item) {
	                            selectedOrder.remove_orderline(item);
	                        });
	                    }
	                    selectedOrder.set_client(null);
	                }
	                if(result && result.pos_normal_receipt_html){
	            		selectedOrder.print_receipt_html = result.pos_normal_receipt_html;
	            		selectedOrder.print_xml_receipt_html = result.pos_xml_receipt_html;
						selectedOrder.print_xml_receipt_payment_lines = result.pos_xml_receipt_payment_lines;
						selectedOrder.print_xml_receipt_taxes_lines = result.pos_xml_receipt_taxes_lines;
	            		selectedOrder.is_reprint = true;
	            		selectedOrder.name = result.pos_reference;
	            		self.gui.show_screen('receipt');
	            	}
	                // if (result && result.lines.length > 0) {
	                //     partner = null;
	                //     if (result.partner_id && result.partner_id[0]) {
	                //         var partner = self.pos.db.get_partner_by_id(result.partner_id[0])
	                //     }
	                //     selectedOrder.set_amount_paid(result.amount_paid);
	                //     selectedOrder.set_amount_return(Math.abs(result.amount_return));
	                //     selectedOrder.set_amount_tax(result.amount_tax);
	                //     selectedOrder.set_amount_total(result.amount_total);
	                //     selectedOrder.set_company_id(result.company_id[1]);
	                //     selectedOrder.set_date_order(result.date_order);
	                //     selectedOrder.set_client(partner);
	                //     selectedOrder.set_pos_reference(result.pos_reference);
	                //     selectedOrder.set_user_name(result.user_id && result.user_id[1]);
	                //     selectedOrder.set_order_note(result.note);
	                //     selectedOrder.set_delivery_date(result.delivery_date);
	                //     selectedOrder.set_delivery_address(result.delivery_address);
                    //     selectedOrder.set_delivery_time(result.delivery_time);
                    //     selectedOrder.set_delivery_type(result.delivery_type);
                    //     selectedOrder.set_delivery_user_id(result.delivery_user_id[0]);
	                //     var statement_ids = [];
	                //     if (result.statement_ids) {
	                //     	var params = {
                	//     		model: 'account.bank.statement.line',
                	//     		method: 'search_read',
                	//     		domain: [['id', 'in', result.statement_ids]],
                	//     	}
                	//     	rpc.query(params, {async: false}).then(function(st){
                	//     		if (st) {
                    //         		_.each(st, function(st_res){
                    //                 	var pymnt = {};
                    //                 	pymnt['amount']= st_res.amount;
                    //                     pymnt['journal']= st_res.journal_id[1];
                    //                     statement_ids.push(pymnt);
                    //         		});
                    //             }
                	//     	}).fail(function(){
                    //         	self.pos.db.notification('danger',"Connection lost");
                    //         });
	                //         selectedOrder.set_journal(statement_ids);
	                //     }
	                //     var params = {
            	    // 		model: 'pos.order.line',
            	    // 		method: 'search_read',
            	    // 		domain: [['id', 'in', result.lines]],
            	    // 	}
            	    // 	rpc.query(params, {async: false}).then(function(lines){
            	    // 		if (lines) {
	                //         	_.each(lines, function(line){
	                //                 var product = self.pos.db.get_product_by_id(Number(line.product_id[0]));
	                //                 var _line = new models.Orderline({}, {pos: self.pos, order: selectedOrder, product: product});
	                //                 _line.set_discount(line.discount);
	                //                 _line.set_quantity(line.qty);
	                //                 _line.set_unit_price(line.price_unit)
	                //                 _line.set_line_note(line.line_note);
	                //                 _line.set_bag_color(line.is_bag);
	                //                 _line.set_return_valid_days(line.return_valid_days);
	                //                 _line.set_deliver_info(line.deliver);
	                //                 if(line && line.is_delivery_product){
	                //                 	_line.set_delivery_charges_color(true);
	                //                 	_line.set_delivery_charges_flag(true);
	                //                 }
	                //                 selectedOrder.add_orderline(_line);
	                //         	});
	                //         }
            	    // 	}).fail(function(){
                    //     	self.pos.db.notification('danger',"Connection lost");
                    //     });
	                //     if(self.pos.config.iface_print_via_proxy){
                    //         var receipt = selectedOrder.export_for_printing();
                    //         var env = {
                    //                 receipt: receipt,
                    //                 widget: self,
                    //                 pos: self.pos,
                    //                 order: self.pos.get_order(),
                    //                 paymentlines: self.pos.get_order().get_paymentlines()
                    //             }
                    //             self.pos.proxy.print_receipt(QWeb.render('XmlReceipt',env));
                    //         self.pos.get('selectedOrder').destroy();    //finish order and go back to scan screen
                    //     }else{
                    //     	self.gui.show_screen('receipt');
                    //     }
	                // }
				} else {
					self.pos.db.notification('danger',_t("No order to print."));
				}
        	};
        	self.pos_graph = function(){
        		self.gui.show_screen('graph_view');
        		self.close_sidebar();
        	};
        	self.x_report = function(){
        		var pos_session_id = [self.pos.pos_session.id];
        		self.pos.chrome.do_action('flexipharmacy.pos_x_report',{additional_context:{
                    active_ids:pos_session_id,
                }}).fail(function(){
                	self.pos.db.notification('danger',"Connection lost");
                });
                if(self.pos.config.iface_print_via_proxy){
                    var pos_session_id = self.pos.pos_session.id;
                    var report_name = "flexipharmacy.pos_x_thermal_report_template";
                    var params = {
                        model: 'ir.actions.report',
                        method: 'get_html_report',
                        args: [pos_session_id, report_name],
                    }
                    rpc.query(params, {async: false})
                    .then(function(report_html){
                        if(report_html && report_html[0]){
                            self.pos.proxy.print_receipt(report_html[0]);
                        }
                    });
                }
        	};
        	self.print_audit_report = function(){
        		self.close_sidebar();
        		self.gui.show_popup('report_popup');
        	};
        	self.print_credit_stmt = function(){
        		self.close_sidebar();
                if(self.pos.get_order().get_client() && self.pos.get_order().get_client().name){
                	self.gui.show_popup('print_credit_detail_popup');
                    var order = self.pos.get_order();
                    order.set_ledger_click(true);
                }else{
                    self.gui.show_screen('clientlist');
                }
        	};
        	self.print_cash_in_out_stmt = function(){
                self.close_sidebar();
                self.gui.show_popup('cash_inout_statement_popup');
        	};
        	self.payment_summary_report = function(){
        		self.close_sidebar();
        		self.gui.show_popup('payment_summary_report_wizard');
        	};
        	self.product_summary_report = function(){
        		self.close_sidebar();
        		self.gui.show_popup('product_summary_report_wizard');
        	};
        	self.order_summary_report = function(){
        		self.close_sidebar();
        		self.gui.show_popup('order_summary_popup');
        	};
        	self.today_sale_report = function(){
        		self.close_sidebar();
        		var str_payment = '';
        		var params = {
    	    		model: 'pos.session',
    	    		method: 'get_session_report',
    	    		args: [],
    	    	}
    	    	rpc.query(params, {async: false}).then(function(result){
		            if(result['error']){
		            	self.pos.db.notification('danger',result['error']);
		            }
		            if(result['payment_lst']){
						var temp = [] ;
						for(var i=0;i<result['payment_lst'].length;i++){
							if(result['payment_lst'][i].session_name){
								if(jQuery.inArray(result['payment_lst'][i].session_name,temp) != -1){
									str_payment+="<tr><td style='font-size: 14px;padding: 8px;'>"+result['payment_lst'][i].journals+"</td>" +
									"<td style='font-size: 14px;padding: 8px;'>"+self.format_currency(result['payment_lst'][i].total.toFixed(2))+"</td>" +
								"</tr>";
								}else{
									str_payment+="<tr><td style='font-size:14px;padding: 8px;' colspan='2'>"+result['payment_lst'][i].session_name+"</td></tr>"+
									"<td style='font-size: 14px;padding: 8px;'>"+result['payment_lst'][i].journals+"</td>" +
									"<td style='font-size: 14px;padding: 8px;'>"+self.format_currency(result['payment_lst'][i].total.toFixed(2))+"</td>" +
								"</tr>";
								temp.push(result['payment_lst'][i].session_name);
								}
							}
						}
					}
		            self.gui.show_popup('pos_today_sale',{result:result,str_payment:str_payment});
		    	}).fail(function(){
                	self.pos.db.notification('danger',"Connection lost");
                });
        	};
        },
        close_sidebar: function(){
        	$("#wrapper").addClass('toggled');
            $('#wrapper').find('i').toggleClass('fa fa-chevron-left fa fa-chevron-right');
        },
        renderElement: function(){
        	var self = this;
        	self._super();
        	self.el.querySelector('#side_username').addEventListener('click', self.click_username);
        	self.el.querySelector('#slidemenubtn').addEventListener('click', self.sidebar_button_click);
        	self.el.querySelector('a#product-screen').addEventListener('click', self.open_product_screen);
        	if(self.pos.config.product_expiry_report && self.pos.get_cashier().access_product_expiry_report){
        		self.el.querySelector('li.expiry_deshboard').addEventListener('click', self.open_expiry_deshboard);
        	}
        	if(self.pos.config.pos_dashboard && self.pos.get_cashier().access_pos_dashboard){
        		self.el.querySelector('li.sales_deshboard').addEventListener('click', self.open_sales_deshboard);
        	}
        	if(self.pos.config.out_of_stock_detail){
        	    self.el.querySelector('a#out_of_stock').addEventListener('click', self.out_of_stock_detail);
        	}
        	if(self.pos.config.enable_int_trans_stock){
        	    self.el.querySelector('a#stock_transfer').addEventListener('click', self.internal_stock_transfer);
        	}
        	if(self.pos.config.enable_gift_card && self.pos.get_cashier().access_gift_card){
        		self.el.querySelector('a#gift_card_screen').addEventListener('click', self.gift_card_screen);
        	}
        	if(self.pos.config.discard_product && self.pos.get_cashier().discard_product){
        		self.el.querySelector('a#discard_product_screen').addEventListener('click', self.discard_product_screen);
        	}
        	if(self.pos.config.enable_gift_voucher && self.pos.get_cashier().access_gift_voucher){
        		self.el.querySelector('a#gift_voucher_screen').addEventListener('click', self.gift_voucher_screen);
        	}
        	if(self.pos.config.enable_reorder && self.pos.get_cashier().access_reorder){
        		self.el.querySelector('a#order-screen').addEventListener('click', self.open_order_screen);
        	}
        	if(self.pos.config.enable_recurrent_order){
        		self.el.querySelector('a#recurrent-order-screen').addEventListener('click', self.recurrent_order_screen);
        	}
        	/*if(self.pos.config.enable_delivery_charges && self.pos.get_cashier().access_delivery_charges){
        	    self.el.querySelector('a#delivery_details_screen').addEventListener('click', self.delivery_details_screen);
        	}*/
            if(self.pos.config.sale_order_operations && self.pos.config.pos_sale_order && self.pos.get_cashier().access_create_so_order){
        		self.el.querySelector('a#all_sale_orders').addEventListener('click', self.all_sale_orders);
        	}
        	if(self.pos.config.sale_order_invoice && self.pos.config.pos_sale_order && self.pos.get_cashier().access_create_so_order){
        		self.el.querySelector('a#all_sale_invoice').addEventListener('click', self.sale_invoice);
        	}
        	if(self.pos.config.enable_print_last_receipt && self.pos.get_cashier().access_print_last_receipt){
        		self.el.querySelector('a#print_lastorder').addEventListener('click', self.print_lastorder);
        	}
        	if(self.el.querySelector('li.pos-graph')){
        		self.el.querySelector('li.pos-graph').addEventListener('click', self.pos_graph);
        	}
        	if(self.el.querySelector('li.x-report')){
        		self.el.querySelector('li.x-report').addEventListener('click', self.x_report);
        	}
        	if(self.el.querySelector('li.today_sale_report')){
        		self.el.querySelector('li.today_sale_report').addEventListener('click', self.today_sale_report);
        	}
        	if(self.el.querySelector('li.payment_summary_report')){
        		self.el.querySelector('li.payment_summary_report').addEventListener('click', self.payment_summary_report);
        	}
        	if(self.el.querySelector('li.product_summary_report')){
        		self.el.querySelector('li.product_summary_report').addEventListener('click', self.product_summary_report);
        	}
        	if(self.el.querySelector('li.order_summary_report')){
        		self.el.querySelector('li.order_summary_report').addEventListener('click', self.order_summary_report);
        	}
        	if(self.el.querySelector('li.print_audit_report')){
        		self.el.querySelector('li.print_audit_report').addEventListener('click', self.print_audit_report);
            }
            if(self.el.querySelector('li.print_credit_stmt')){
        		self.el.querySelector('li.print_credit_stmt').addEventListener('click', self.print_credit_stmt);
        	}
        	if(self.pos.config.money_in_out && self.pos.get_cashier().access_print_cash_statement){
        		self.el.querySelector('li.print_cash_in_out_stmt').addEventListener('click', self.print_cash_in_out_stmt);
            }
            if(self.pos.config.enable_change_pin){
        		self.el.querySelector('a#user_change_pin').addEventListener('click', self.user_change_pin);
        	}
        	$('.main_slider-ul').click(function() {
        	    $(this).find('ul.content-list-ul').slideToggle();
//        	    $(this).find('i').toggleClass('fa fa-chevron-down fa fa-chevron-right');
        	    /*if($('#toggle_image').hasClass('right')){
        	    	$('#toggle_image').removeClass('right');
        	    	$('#toggle_image').attr('src','/flexipharmacy/static/src/img/icons/angle-down.svg')
        	    }else{
        	    	$('#toggle_image').addClass('right');
        	    	$('#toggle_image').attr('src','/flexipharmacy/static/src/img/icons/angle-right.png')
        	    }*/
        	});
        },
	});

    var PosCartCountWidget = PosBaseWidget.extend({
        template: 'PosCartCountWidget',
        init: function(parent, options){
            var self = this;
            this._super(parent,options);
            self.show_cart = function(){
            	var order = self.pos.get_order();
            	if(order.is_empty()) {
            		return;
            	}
            	if(self.gui.get_current_screen() != 'products'){
            		var html_data = $('.order-scroller').html();
                	$('.show-left-cart').html('').append(html_data);
                	$('.show-left-cart').toggle("slide");
            	}
            };
        },
        renderElement: function(){
        	var self = this;
        	self._super();
        	$(".pos-cart-info").delegate( "#pos-cart", "click",self.show_cart);
        },
    });

    chrome.HeaderButtonWidget.include({
		renderElement: function(){
	        var self = this;
	        this._super();
	        if(this.action){
	            this.$el.click(function(){
	            	self.gui.show_popup('POS_session_config');
	            });
	        }
	    },
	});

    chrome.OrderSelectorWidget.include({
    	start: function(){
            this._super();
            var customer_display = this.pos.config.customer_display;
            if(this.pos.get_order()){
            	if(customer_display){
            		this.pos.get_order().mirror_image_data();
            	}
            }
    	},
    	deleteorder_click_handler: function(event, $el) {
            var self  = this;
            $('.show-left-cart').hide();
            if(self.gui.get_current_screen() == "receipt"){
            	return
            }
            var order = this.pos.get_order();
            var customer_display = this.pos.config.customer_display;
            if (!order) {
                return;
            } else if ( !order.is_empty() ){
                this.gui.show_popup('confirm',{
                    'title': _t('Destroy Current Order ?'),
                    'body': _t('You will lose any data associated with the current order'),
                    confirm: function(){
                        self.pos.delete_current_order();
                        if(customer_display){
                        	self.pos.get_order().mirror_image_data();
                        }
                        $('#slidemenubtn1').css({'right':'0px'});
                        $('.product-list-container').css('width','100%');
                        $('#wrapper1').addClass('toggled');
                    },
                });
            } else {
                this.pos.delete_current_order();
                if(customer_display){
                	self.pos.get_order().mirror_image_data();
                }
                $('#slidemenubtn1').css({'right':'0px'});
                $('.product-list-container').css('width','100%');
                $('#wrapper1').addClass('toggled');
            }
        },
        renderElement: function(){
            var self = this;
            this._super();
            var customer_display = this.pos.config.customer_display;
            this.$('.order-button.select-order').click(function(event){
             	if(self.pos.get_order() && customer_display){
             		self.pos.get_order().mirror_image_data(true);
             	}
            });
            this.$('.neworder-button').click(function(event){
             	if(self.pos.get_order() && customer_display){
             		self.pos.get_order().mirror_image_data(true);
             	}
            });
            this.$('.deleteorder-button').click(function(event){
             	if(self.pos.get_order() && customer_display){
             		self.pos.get_order().mirror_image_data(true);
             	}
            });
            if(this.pos.config.enable_automatic_lock && self.pos.get_cashier().access_pos_lock){
                var time_interval = this.pos.config.time_interval || 3;
                start_lock_timer(time_interval,self);
            }
            // Click on Manual Lock button
            $('.order-button.lock_button').click(function(){
            	self.gui.show_popup('lock_popup');
            });
            // Click on Unlock button
            $('.unlock_button').click(function(){
                $('.freeze_screen').removeClass("active_state");
                $('.unlock_button').hide();
                $('.unlock_button').css('z-index',0);
                self.gui.show_screen('login');
                $('.get-input').focus();
            });
        },
    });

});