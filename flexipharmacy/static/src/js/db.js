odoo.define('flexipharmacy.db', function (require) {
	"use strict";

	var DB = require('point_of_sale.DB');
	var core = require('web.core');
	var rpc = require('web.rpc');

	var _t = core._t;

	DB.include({
		init: function(options){
	        this._super.apply(this, arguments);
	        this.pay_button_by_id = {};
	        this.currency_symbol = {};
	        this.group_products = [];
        	this.order_write_date = null;
        	this.order_by_id = {};
        	this.line_by_id = {};
        	this.order_sorted = [];
        	this.order_search_string = "";
        	this.line_search_string = ""
            this.product_search_string = "";
            this.product_search_string_desc = "";
        	this.doctor_by_id = {};
        	this.doctor_search_string = "";
        	this.all_categories = [];
        	this.all_brands = [];
        	this.products_by_brand_id = {};
        	this.brands_search_list =[];
        	this.product_namelist = [];
        	this.dummy_product_ids = [];
        	this.product_write_date = '';
//        	Gift Card
        	this.card_products = [];
            this.card_write_date = null;
            this.card_by_id = {};
            this.card_sorted = [];
            this.card_search_string = "";
            this.gift_card_cust_search_string = "";
//            Voucher
            this.voucher_write_date = null;
            this.voucher_by_id = {};
            this.voucher_sorted = [];
            this.voucher_search_string = "";

            this.partners_name = [];
            this.partner_by_name = {};
            this.all_partners = [];
//          Stock Picking Data
            this.stock_picking_by_id = {};
            this.picking_sorted = [];
            this.picking_search_string = "";
            this.expire_categ_by_id = {};
            this.expire_categ_string = "";
            this.product_detail_search_string = "";
            this.product_expire_detail_by_id = {};
//          Internal Stock Transfer
            this.picking_type_by_id = {};
//          Sale order extension
            this.sale_order_write_date = null;
        	this.sale_order_by_id = {};
        	this.sale_order_sorted = [];
        	this.sale_order_search_string = "";

        	this.sale_invoice_write_date = null;
        	this.sale_invoice_by_id = {};
        	this.sale_invoice_sorted = [];
        	this.sale_invoice_search_string = "";
        	this.all_product = []
//        	Recurrent Order
            this.recurrent_order_products = [];
            this.recurrent_order_write_date = null;
            this.recurrent_order_by_id = {};
            this.recurrent_order_sorted = [];
            this.recurrent_order_search_string = "";
//            Product Variant
            this.template_by_id = {};
            this.product_attribute_by_id = {};
            this.product_attribute_value_by_id = {};
            this.pay_button_by_id = {};

	    },
	    add_picking_types: function(stock_pick_typ){
            var self = this;
            stock_pick_typ.map(function(type){
                self.picking_type_by_id[type.id] = type;
            });
	    },
	    get_picking_type_by_id: function(id){
            return this.picking_type_by_id[id]
        },
	    search_product: function(query){
            try {
                query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g,'.');
                query = query.replace(' ','.+');
                var re = RegExp("([0-9]+):.*?"+query,"gi");
            }catch(e){
                return [];
            }
            var results = [];
            for(var i = 0; i < this.limit; i++){
                var r = re.exec(this.product_search_string);
                if(r){
                    var id = Number(r[1]);
                    results.push(this.get_product_by_id(id));
                }else{
                    break;
                }
            }
            return results;
        },
        get_doctors_list: function(){
            var self = this;
            var doctor_list = [];
            var doctor;
            self.doctor_search_string = '';
            var params = {
                model: 'res.partner',
                method: 'search_read',
                domain: [['is_doctor','=',true],['supplier','=',true]],
                fields: ['name','city','mobile','phone','street','email','country_id',
                        'property_product_pricelist','vat','zip','barcode'],
            }
            rpc.query(params, {async: false})
            .then(function(doctors){
                if(doctors && doctors.length > 0){
                    for(var i = 0, len = doctors.length; i < len; i++){
                        doctor = doctors[i];
                        doctor['address'] = (doctor.street || '') +', '+
                                  (doctor.zip || '')    +' '+
                                  (doctor.city || '')   +', '+
                                  (doctor.country_id[1] || '');
                        doctor_list.push(doctor);
                        self.doctor_by_id[doctor.id] = doctor;
                        self.doctor_search_string += self._doctor_search_string(doctor);
                    }
                }
            });
            return doctor_list;
        },
        search_doctor: function(query){
            try {
                query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g,'.');
                query = query.replace(/ /g,'.+');
                var re = RegExp("([0-9]+):.*?"+query,"gi");
            }catch(e){
                return [];
            }
            var results = [];
            for(var i = 0; i < this.limit; i++){
                var r = re.exec(this.doctor_search_string);
                if(r){
                    var id = Number(r[1]);
                    results.push(this.doctor_by_id[id]);
                }else{
                    break;
                }
            }
            return results;
        },
        _doctor_search_string: function(doctor){
            var str =  doctor.name;
            if(doctor.barcode){
                str += '|' + doctor.barcode;
            }
            if(doctor.address){
                str += '|' + doctor.address;
            }
            if(doctor.phone){
                str += '|' + doctor.phone.split(' ').join('');
            }
            if(doctor.mobile){
                str += '|' + doctor.mobile.split(' ').join('');
            }
            if(doctor.email){
                str += '|' + doctor.email;
            }
            if(doctor.vat){
                str += '|' + doctor.vat;
            }
            str = '' + doctor.id + ':' + str.replace(':','') + '\n';
            return str;
        },
        get_supplier_list: function(){
            var supplier_list = [];
            var params = {
                model: 'res.partner',
                method: 'search_read',
                domain: [['supplier','=','True']],
                fields: ['name','city','mobile','phone','street','email','country_id',
                        'remaining_loyalty_points','remaining_wallet_amount',
                        'property_product_pricelist','vat','zip','credit_limit','barcode'],
            }
            rpc.query(params, {async: false})
            .then(function(supplier){
                if(supplier && supplier[0]){
                     _.each(supplier, function(each_supplier){
                        supplier_list.push({
                            'id':each_supplier.id,
                            'value':each_supplier.name,
                            'label':each_supplier.name,
                        });
                     });
                }
            });
            return supplier_list;
        },
	    get_product_write_date: function(){
            return this.product_write_date || "1970-01-01 00:00:00";
        },
	    get_category_search_list: function(){
            var category_search_list = [];
            _.each(this.all_categories, function(category){
                category_search_list.push({
                    'id':category.id,
                    'value':category.name,
                    'label':category.name,
            	});
            });
            return category_search_list;
        },
	    get_all_categories : function() {
			return this.all_categories;
		},
	    add_categories: function(categories){
	    	this._super(categories);
	    	this.all_categories = categories;
	    },
	    add_brands: function(brands){
	    	var self = this;
	    	this.all_brands = brands;
	    	_.each(brands, function(brand){
	    		self.products_by_brand_id[brand.id] = [];
	    		self.brands_search_list.push({
                    'id':brand.id,
                    'value':brand.name,
                    'label':brand.name,
            	});
	    	});
	    },
	    get_barnds_search_list: function(){
            return this.brands_search_list;
        },
        get_products_by_brand_id: function(id){
        	return this.products_by_brand_id[id];
        },
	    add_quick_payment: function(quick_pays){
	    	var self = this;
	    	quick_pays.map(function(pay){
	    		self.pay_button_by_id[pay.id] = pay
	    	});
	    },
	    get_button_by_id: function(id){
	    	return this.pay_button_by_id[id]
	    },
	    get_product_namelist: function(){
	    	return this.product_namelist;
	    },
	    get_dummy_product_ids: function(){
	    	return this.dummy_product_ids;
	    },
	    add_products: function(products){
            var new_write_date = '';
            var product;
            for(var i = 0, len = products.length; i < len; i++){
                product = products[i];
                var symbol = this.currency_symbol ? this.currency_symbol.symbol : "$";
                product.list_price = product.lst_price || product.list_price;
                if(product.list_price) {
                	product.price = product.list_price;
                	var unit_name = product.uom_id[1] ? product.uom_id[1] : "";
                	if(product.to_weight){
                		if(this.currency_symbol && this.currency_symbol.position == "after"){
                			$("[data-product-id='"+product.id+"']").find('.price-tag').html(product['list_price'].toFixed(2)+" "+symbol+'/'+unit_name);
                		} else{
                			$("[data-product-id='"+product.id+"']").find('.price-tag').html(symbol+" "+product['list_price'].toFixed(2)+'/'+unit_name);
                		}
                	} else {
                		if(this.currency_symbol && this.currency_symbol.position == "after"){
                			$("[data-product-id='"+product.id+"']").find('.price-tag').html(product['list_price'].toFixed(2)+" "+symbol);
                		} else{
                			$("[data-product-id='"+product.id+"']").find('.price-tag').html(symbol+" "+product['list_price'].toFixed(2)+'/'+unit_name);
                		}
                    }
                    if (product.id==26015){
                        console.log('PRODUCTO --------', product.qty_available)
                    }
                    $("[data-product-id='"+product.id+"']").find('.stock_qty').html(product.qty_available);
                    if (product.product_brand_id[1] != undefined){
                        $("[data-product-id='"+product.id+"']").find('.product-name').html(
                            '<strong><span class="product_list_brand_name">'+product.product_brand_id[1]+'</span></strong><br />'
                            +
                            product.display_name);
                    }else{
                        $("[data-product-id='"+product.id+"']").find('.product-name').html(product.display_name);
                    }
                }
                product.original_name = product.product_tmpl_id[1];
                if(!product.is_dummy_product){
                	this.product_namelist.push([product.id,product.display_name]);
                }else{
                	this.dummy_product_ids.push(product.id);
                }

                this.product_search_string += this._product_name_search_string(product);
                this.product_search_string_desc += this._product_search_string(product);

                if (this.product_write_date &&
                    this.product_by_id[product.id] &&
                    new Date(this.product_write_date).getTime() + 1000 >=
                    new Date(product.write_date).getTime() ) {
                    continue;
                } else if ( new_write_date < product.write_date ) {
                    new_write_date  = product.write_date;
                }
                //Setup for product brands
                if(product.product_brand_id && product.product_brand_id[0]){
                	if(this.products_by_brand_id[product.product_brand_id[0]]){
                		this.products_by_brand_id[product.product_brand_id[0]].push(product);
                	} else{
                		this.products_by_brand_id[product.product_brand_id[0]] = [product];
                	}

                }
	        }
	        this.product_write_date = new_write_date || this.product_write_date;
	        this._super(products);
        },
		notification: function(type, message){
        	var types = ['success','warning','info', 'danger'];
        	if($.inArray(type.toLowerCase(),types) != -1){
        		$('div.span4').remove();
        		var newMessage = '';
        		message = _t(message);
        		switch(type){
        		case 'success' :
        			newMessage = '<i class="fa fa-check" aria-hidden="true"></i> '+message;
        			break;
        		case 'warning' :
        			newMessage = '<i class="fa fa-exclamation-triangle" aria-hidden="true"></i> '+message;
        			break;
        		case 'info' :
        			newMessage = '<i class="fa fa-info" aria-hidden="true"></i> '+message;
        			break;
        		case 'danger' :
        			newMessage = '<i class="fa fa-ban" aria-hidden="true"></i> '+message;
        			break;
        		}
	        	$('body').append('<div class="span4 pull-right">' +
	                    '<div class="alert alert-'+type+' fade">' +
	                    newMessage+
	                   '</div>'+
	                 '</div>');
        	    $(".alert").removeClass("in").show();
        	    $(".alert").delay(200).addClass("in").fadeOut(5000);
        	}
        },
        add_orders: function(orders){
            var updated_count = 0;
            var new_write_date = '';
            for(var i = 0, len = orders.length; i < len; i++){
                var order = orders[i];
                if (    this.order_write_date && 
                        this.order_by_id[order.id] &&
                        new Date(this.order_write_date).getTime() + 1000 >=
                        new Date(order.write_date).getTime() ) {
                    continue;
                } else if ( new_write_date < order.write_date ) { 
                    new_write_date  = order.write_date;
                }
                if (!this.order_by_id[order.id]) {
                    this.order_sorted.push(order.id);
                }
                this.order_by_id[order.id] = order;
                updated_count += 1;
            }
            this.order_write_date = new_write_date || this.order_write_date;
            if (updated_count) {
                // If there were updates, we need to completely 
                this.order_search_string = "";
                for (var id in this.order_by_id) {
                    var order = this.order_by_id[id];
                    this.order_search_string += this._order_search_string(order);
                }
            }
            return updated_count;
        },
        _order_search_string: function(order){
            var str =  order.name;
            if(order.pos_reference){
                str += '|' + order.pos_reference;
            }
            if(order.partner_id.length > 0){
                str += '|' + order.partner_id[1];
            }
            str = '' + order.id + ':' + str.replace(':','') + '\n';
            return str;
        },
        get_order_write_date: function(){
            return this.order_write_date;
        },
        get_order_by_id: function(id){
            return this.order_by_id[id];
        },
        search_order: function(query){
            try {
                query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g,'.');
                query = query.replace(' ','.+');
                var re = RegExp("([0-9]+):.*?"+query,"gi");
            }catch(e){
                return [];
            }
            var results = [];
            var r;
            for(var i = 0; i < this.limit; i++){
                r = re.exec(this.order_search_string);
                if(r){
                    var id = Number(r[1]);
                    results.push(this.get_order_by_id(id));
                }else{
                    break;
                }
            }
            return results;
        },
        add_reserved_items: function(lines){
        	for(var i = 0, len = lines.length; i < len; i++){
        		var line = lines[i];
        		this.line_search_string += this._line_search_string(line);
        		this.line_by_id[line.id] = line
        	}
        },
        _line_search_string: function(line){
        	var str =  line.name;
        	if(line.product_id.length > 0){
                str += '|' + line.product_id[1];
            }
        	if(line.order_id.length > 0){
                str += '|' + line.order_id[1];
            }
        	str = '' + line.id + ':' + str.replace(':','') + '\n';
            return str;
        },
        search_item: function(query){
            try {
                query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g,'.');
                query = query.replace(' ','.+');
                var re = RegExp("([0-9]+):.*?"+query,"gi");
            }catch(e){
                return [];
            }
            var results = [];
            var r;
            for(var i = 0; i < this.limit; i++){
                r = re.exec(this.line_search_string);
                if(r){
                    var id = Number(r[1]);
                    results.push(this.line_by_id[id]);
                }else{
                    break;
                }
            }
            return results;
        },
        add_partners: function(partners){
			var self = this;
			for(var i = 0, len = partners.length; i < len; i++){
	            var partner = partners[i];
	            var old_partner = this.partner_by_id[partner.id];
	            if(partners && old_partner && partner.total_remaining_points !== old_partner.total_remaining_points){
	            	old_partner['total_remaining_points'] = partner.total_remaining_points;
	            }
	            if(partner.name){
        			self.partners_name.push(partner.name);
        			self.partner_by_name[partner.name] = partner;
        		}
        		this.gift_card_cust_search_string += this._gift_card_cust_search_string(partner);
			}
			if(partners.length > 0){
        		_.extend(this.all_partners, partners)
        	}
			return this._super(partners);
		},
		get_partners_name: function(){
        	return this.partners_name;
        },
        get_partner_by_name: function(name){
            if(this.partner_by_name[name]){
                return this.partner_by_name[name];
            }
            return undefined;
        },
        _gift_card_cust_search_string: function(partner){
            var str = '';
		    if(partner){
		        if(partner.name){
                    str =  partner.name;
                }
                if(partner.mobile){
                    str += '|' + partner.mobile;
                }
                if(partner.email){
                    str += '|' + partner.email;
                }
                str = '' + partner.id + ':' + str.replace(':','') + '\n';
                return str;
            } else{
                return str;
            }
        },
        search_gift_card_customer: function(query){
            try {
                query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g,'.');
                query = query.replace(' ','.+');
                var re = RegExp("([0-9]+):.*?"+query,"gi");
            }catch(e){
                return [];
            }
            var results = [];
            var r;
            for(var i = 0; i < this.limit; i++){
                r = re.exec(this.gift_card_cust_search_string);
                if(r){
                    var id = Number(r[1]);
                    results.push(this.partner_by_id[id]);
                }else{
                    break;
                }
            }
            return results;
        },
        add_giftcard: function(gift_cards){
            var updated_count = 0;
            var new_write_date = '';
            for(var i = 0, len = gift_cards.length; i < len; i++){
                var gift_card = gift_cards[i];
                if (    this.card_write_date && 
                        this.card_by_id[gift_card.id] &&
                        new Date(this.card_write_date).getTime() + 1000 >=
                        new Date(gift_card.write_date).getTime() ) {
                    continue;
                } else if ( new_write_date < gift_card.write_date ) { 
                    new_write_date  = gift_card.write_date;
                }
                if (!this.card_by_id[gift_card.id]) {
                    this.card_sorted.push(gift_card.id);
                }
                this.card_by_id[gift_card.id] = gift_card;
                updated_count += 1;
            }
            this.card_write_date = new_write_date || this.card_write_date;
            if (updated_count) {
                // If there were updates, we need to completely 
                this.card_search_string = "";
                for (var id in this.card_by_id) {
                    var gift_card = this.card_by_id[id];
                    this.card_search_string += this._card_search_string(gift_card);
                }
            }
            return updated_count;
        },
        _card_search_string: function(gift_card){
            var str =  gift_card.card_no;
            if(gift_card.customer_id){
                str += '|' + gift_card.customer_id[1];
            }
            str = '' + gift_card.id + ':' + str.replace(':','') + '\n';
            return str;
        },
        get_card_write_date: function(){
            return this.card_write_date;
        },
        get_card_by_id: function(id){
            return this.card_by_id[id];
        },
        search_gift_card: function(query){
            try {
                query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g,'.');
                query = query.replace(' ','.+');
                var re = RegExp("([0-9]+):.*?"+query,"gi");
            }catch(e){
                return [];
            }
            var results = [];
            var r;
            for(var i = 0; i < this.limit; i++){
                r = re.exec(this.card_search_string);
                if(r){
                    var id = Number(r[1]);
                    results.push(this.get_card_by_id(id));
                }else{
                    break;
                }
            }
            return results;
        },
        add_gift_vouchers: function(gift_vouchers){
            var updated_count = 0;
            var new_write_date = '';
            for(var i = 0, len = gift_vouchers.length; i < len; i++){
                var gift_voucher = gift_vouchers[i];
                if (    this.voucher_write_date &&
                        this.voucher_by_id[gift_voucher.id] &&
                        new Date(this.voucher_write_date).getTime() + 1000 >=
                        new Date(gift_voucher.write_date).getTime() ) {
                    continue;
                } else if ( new_write_date < gift_voucher.write_date ) {
                    new_write_date  = gift_voucher.write_date;
                }
                if (!this.voucher_by_id[gift_voucher.id]) {
                    this.voucher_sorted.push(gift_voucher.id);
                }
                this.voucher_by_id[gift_voucher.id] = gift_voucher;
                updated_count += 1;
            }
            this.voucher_write_date = new_write_date || this.voucher_write_date;
            if (updated_count) {
                // If there were updates, we need to completely
                this.voucher_search_string = "";
                for (var id in this.voucher_by_id) {
                    var gift_voucher = this.voucher_by_id[id];
                    this.voucher_search_string += this._voucher_search_string(gift_voucher);
                }
            }
            return updated_count;
        },
        _voucher_search_string: function(gift_voucher){
            var str =  gift_voucher.voucher_name;
            if(gift_voucher.voucher_code){
                str += '|' + gift_voucher.voucher_code;
            }
            str = '' + gift_voucher.id + ':' + str.replace(':','') + '\n';
            return str;
        },
        get_voucher_write_date: function(){
            return this.voucher_write_date;
        },
        get_voucher_by_id: function(id){
            return this.voucher_by_id[id];
        },
        search_gift_vouchers: function(query){
            try {
                query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g,'.');
                query = query.replace(' ','.+');
                var re = RegExp("([0-9]+):.*?"+query,"gi");
            }catch(e){
                return [];
            }
            var results = [];
            var r;
            for(var i = 0; i < this.limit; i++){
                r = re.exec(this.voucher_search_string);
                if(r){
                    var id = Number(r[1]);
                    results.push(this.get_voucher_by_id(id));
                }else{
                    break;
                }
            }
            return results;
        },
        add_recurrent_order: function(recurrent_orders){
            var updated_count = 0;
            var new_write_date = '';
            for(var i = 0, len = recurrent_orders.length; i < len; i++){
                var recurrent_order = recurrent_orders[i];
                if (    this.recurrent_order_write_date &&
                        this.recurrent_order_by_id[recurrent_order.id] &&
                        new Date(this.recurrent_order_write_date).getTime() + 1000 >=
                        new Date(recurrent_order.write_date).getTime() ) {
                    continue;
                } else if ( new_write_date < recurrent_order.write_date ) {
                    new_write_date  = recurrent_order.write_date;
                }
//                if (!this.recurrent_order_by_id[recurrent_order.id]) {
//                    this.card_sorted.push(recurrent_order.id);
//                }
                this.recurrent_order_by_id[recurrent_order.id] = recurrent_order;
                updated_count += 1;
            }
            this.recurrent_order_write_date = new_write_date || this.recurrent_order_write_date;
            if (updated_count) {
                // If there were updates, we need to completely
                this.recurrent_order_search_string = "";
                for (var id in this.recurrent_order_by_id) {
                    var recurrent_order = this.recurrent_order_by_id[id];
                    this.recurrent_order_search_string += this._recurrent_order_search_string(recurrent_order);
                }
            }
            return updated_count;
        },

        _recurrent_order_search_string: function(recurrent_order){
            var str =  "";//recurrent_order.card_no;
            if(recurrent_order.partner_id){
                str += '|' + recurrent_order.partner_id[1];
            }
            str = '' + recurrent_order.id + ':' + str.replace(':','') + '\n';
            return str;
        },

        recurrent_order_write_date: function(){
            return this.recurrent_order_write_date;
        },

        get_recurrent_order_by_id: function(id){
            return this.recurrent_order_by_id[id];
        },

        search_recurrent_order: function(query){
            try {
                query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g,'.');
                query = query.replace(' ','.+');
                var re = RegExp("([0-9]+):.*?"+query,"gi");
            }catch(e){
                return [];
            }
            var results = [];
            var r;
            for(var i = 0; i < this.limit; i++){
                r = re.exec(this.recurrent_order_search_string);
                if(r){
                    var id = Number(r[1]);
                    results.push(this.get_recurrent_order_by_id(id));
                }else{
                    break;
                }
            }
            return results;
        },
//        Stock Picking Screen Data
        add_stock_picking: function(stock_picking){
            var updated_count = 0;
            var new_write_date = '';
            for(var i = 0, len = stock_picking.length; i < len; i++){
                var stockpicking_data = stock_picking[i];
                if (    this.stock_picking_by_id[stockpicking_data.id]) {
                    continue;
                } else if ( new_write_date < stockpicking_data.write_date ) {
                    new_write_date  = stockpicking_data.write_date;
                }
                if (!this.stock_picking_by_id[stockpicking_data.id]) {
                    this.picking_sorted.push(stockpicking_data.id);
                }
                this.stock_picking_by_id[stockpicking_data.id] = stockpicking_data;
                updated_count += 1;
            }
            if (updated_count) {
                // If there were updates, we need to completely
                this.picking_search_string = "";
                for (var id in this.stock_picking_by_id) {
                    var stockpicking_data = this.stock_picking_by_id[id];
                    this.picking_search_string += this._picking_search_string(stockpicking_data);
                }
            }
            return updated_count;
        },
        _picking_search_string: function(stockpicking_data){
	    	var str =  stockpicking_data.name;
	        if(str){
	        	str = '' + stockpicking_data.id + ':' + str.replace(':','') + '\n';
		        return str;
	        }
	        return false
	    },
        get_picking_by_id: function(id){
            return this.stock_picking_by_id[id];
        },
        search_stock_picking: function(query){
            try {
                query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g,'.');
                query = query.replace(' ','.+');
                var re = RegExp("([0-9]+):.*?"+query,"gi");
            }catch(e){
                return [];
            }
            var results = [];
            var r;
            for(var i = 0; i < this.limit; i++){
                r = re.exec(this.picking_search_string);
                if(r){
                    var id = Number(r[1]);
                    results.push(this.get_picking_by_id(id));
                }else{
                    break;
                }
            }
            return results;
        },
        add_expire_categ: function(expire_categ){
            var updated_count = 0;
            for(var i = 0, len = expire_categ.length; i < len; i++){
                var expire_cat = expire_categ[i];
                this.expire_categ_by_id[expire_cat.categ_id] = expire_cat;
                updated_count += 1;
            }
            if (updated_count) {
            	this.expire_categ_string = "";
                for (var id in this.expire_categ_by_id) {
                    var expire_categ = this.expire_categ_by_id[id];
                    this.expire_categ_string += this._expire_categ_string(expire_categ);
                }
            }
            return updated_count;
        },
        _expire_categ_string: function(expire_categ){
        	var str =  expire_categ.categ_name;
            str = '' + expire_categ.categ_id + ':' + str.replace(':','') + '\n';
            return str;
        },
        search_exprire_categories: function(query){
            try {
                query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g,'.');
                query = query.replace(' ','.+');
                var re = RegExp("([0-9]+):.*?"+query,"gi");
            }catch(e){
                return [];
            }
            var results = [];
            var r;
            for(var i = 0; i < this.limit; i++){
                r = re.exec(this.expire_categ_string);
                if(r){
                    var id = Number(r[1]);
                    results.push(this.get_expire_categ_by_id(id));
                }else{
                    break;
                }
            }
            return results;
        },
        get_expire_categ_by_id: function(id){
        	return this.expire_categ_by_id[id];
        },
        add_detail_product_list: function(product_list){
            var updated_count = 0;
            for(var i = 0, len = product_list.length; i < len; i++){
                var product = product_list[i];
                this.product_expire_detail_by_id[product.product_id[0]] = product
                updated_count += 1;
            }
            if (updated_count) {
            	this.product_detail_search_string = "";
                for (var id in this.product_expire_detail_by_id) {
                    var product = this.product_expire_detail_by_id[id];
                    this.product_detail_search_string += this._product_detail_search_string(product);
                }
            }
            return updated_count;
        },
        _product_detail_search_string: function(product){
        	var str =  product.product_id[1];
        	if(product.lot_id){
                str += '|' + product.lot_id[1];
            }
            str = '' + product.product_id[0] + ':' + str.replace(':','') + '\n';
            return str;
        },
        get_product_expire_detail_by_id: function(id){
        	return this.product_expire_detail_by_id[id];
        },
        search_detail_product_list: function(query){
            try {
                query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g,'.');
                query = query.replace(' ','.+');
                var re = RegExp("([0-9]+):.*?"+query,"gi");
            }catch(e){
                return [];
            }
            var results = [];
            var r;
            for(var i = 0; i < this.limit; i++){
                r = re.exec(this.product_detail_search_string);
                if(r){
                    var id = Number(r[1]);
                    results.push(this.get_product_expire_detail_by_id(id));
                }else{
                    break;
                }
            }
            return results;
        },
//    	Sale order extension
    	add_sale_orders: function(orders){
            var updated_count = 0;
            var new_write_date = '';
            if(orders && orders.length > 0){
                for(var i = 0, len = orders.length; i < len; i++){
                    var order = orders[i];
                    if (this.sale_order_write_date &&
                            this.sale_order_by_id[order.id] &&
                            new Date(this.sale_order_write_date).getTime() + 1000 >=
                            new Date(order.write_date).getTime() ) {
                        continue;
                    } else if ( new_write_date < order.write_date ) {
                        new_write_date  = order.write_date;
                    }
                    if (!this.sale_order_by_id[order.id]) {
                        this.sale_order_sorted.push(order.id);
                    }
                    this.sale_order_by_id[order.id] = order;
                    updated_count += 1;
                }
            }
            this.sale_order_write_date = new_write_date || this.sale_order_write_date;
            if (updated_count) {
                // If there were updates, we need to completely
                this.sale_order_search_string = "";
                for (var id in this.sale_order_by_id) {
                    var order = this.sale_order_by_id[id];
                    this.sale_order_search_string += this._sale_order_search_string(order);
                }
            }
            return updated_count;
        },
        add_sale_invoices: function(invoices){
            var updated_count = 0;
            var new_write_date = '';
            for(var i = 0, len = invoices.length; i < len; i++){
                var invoice = invoices[i];
                if (    this.sale_invoice_write_date &&
                        this.sale_invoice_by_id[invoice.id] &&
                        new Date(this.sale_invoice_write_date).getTime() + 1000 >=
                        new Date(invoice.write_date).getTime() ) {
                    continue;
                } else if ( new_write_date < invoice.write_date ) {
                    new_write_date  = invoice.write_date;
                }
                if (!this.sale_invoice_by_id[invoice.id]) {
                    this.sale_invoice_sorted.push(invoice.id);
                }
                this.sale_invoice_by_id[invoice.id] = invoice;
                updated_count += 1;
            }
            this.sale_invoice_write_date = new_write_date || this.sale_invoice_write_date;
            if (updated_count) {
                // If there were updates, we need to completely
                this.sale_invoice_search_string = "";
                for (var id in this.sale_invoice_by_id) {
                    var invoice = this.sale_invoice_by_id[id];
                    this.sale_invoice_search_string += this._sale_invoice_search_string(invoice);
                }
            }
            return updated_count;
        },
        _sale_order_search_string: function(order){
            var str =  order.name;
            if(order.partner_id){
                str += '|' + order.partner_id[1];
            }
            str = '' + order.id + ':' + str.replace(':','') + '\n';
            return str;
        },
        _sale_invoice_search_string: function(invoice){
            var str =  invoice.display_name;
            if(invoice.partner_id){
                str += '|' + invoice.partner_id[1];
            }
            str = '' + invoice.id + ':' + str.replace(':','') + '\n';
            return str;
        },
        get_sale_order_write_date: function(){
            return this.sale_order_write_date;
        },
        get_sale_invoice_write_date: function(){
            return this.sale_invoice_write_date;
        },
        get_sale_order_by_id: function(id){
            return this.sale_order_by_id[id];
        },
        get_sale_invoice_by_id: function(id){
            return this.sale_invoice_by_id[id];
        },
        search_sale_order: function(query){
            try {
                query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g,'.');
                query = query.replace(' ','.+');
                var re = RegExp("([0-9]+):.*?"+query,"gi");
            }catch(e){
                return [];
            }
            var results = [];
            var r;
            for(var i = 0; i < this.limit; i++){
                r = re.exec(this.sale_order_search_string);
                if(r){
                    var id = Number(r[1]);
                    results.push(this.get_sale_order_by_id(id));
                }else{
                    break;
                }
            }
            return results;
        },
        search_invoice: function(query){
            try {
                query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g,'.');
                query = query.replace(' ','.+');
                var re = RegExp("([0-9]+):.*?"+query,"gi");
            }catch(e){
                return [];
            }
            var results = [];
            var r;
            for(var i = 0; i < this.limit; i++){
                r = re.exec(this.sale_invoice_search_string);
                if(r){
                    var id = Number(r[1]);
                    results.push(this.get_sale_invoice_by_id(id));
                }else{
                    break;
                }
            }
            return results;
        },
        get_all_product: function(){
            return this.all_product
        },
        get_product_by_value_and_products: function(value_id, products){
            var list = [];
            for (var i = 0, len = products.length; i < len; i++) {
                if (products[i].attribute_value_ids.indexOf(value_id) != -1){
                    list.push(products[i]);
                }
            }
            return list;
        },

        get_product_attribute_by_id: function(attribute_id){
            return this.product_attribute_by_id[attribute_id];
        },

        get_product_attribute_value_by_id: function(attribute_value_id){
            return this.product_attribute_value_by_id[attribute_value_id];
        },

        get_product_by_ids: function(product_ids){
            var list = [];
            for (var i = 0, len = product_ids.length; i < len; i++) {
                list.push(this.product_by_id[product_ids[i]]);
            }
            return list;
        },


        attribute_by_template_id: function(template_id){
            var template = this.template_by_id[template_id];
            return this.attribute_by_attribute_value_ids(template.attribute_value_ids);
        },

        attribute_by_attribute_value_ids: function(value_ids){
            var attribute_ids = [];
            for (var i = 0; i < value_ids.length; i++){
                var value = this.product_attribute_value_by_id[value_ids[i]];
                if (attribute_ids.indexOf(value.attribute_id[0])==-1){
                    attribute_ids.push(value.attribute_id[0]);
                }
            }
            return attribute_ids;
        },

        add_templates: function(templates){
            for(var i=0 ; i < templates.length; i++){
                var attribute_value_ids = [];
                // store Templates
                this.template_by_id[templates[i].id] = templates[i];

                // Update Product information
                for (var j = 0; j <templates[i].product_variant_ids.length; j++){
                    var product = this.product_by_id[templates[i].product_variant_ids[j]];
                    if(product){
                    	for (var k = 0; k < product.attribute_value_ids.length; k++){
                            if (attribute_value_ids.indexOf(product.attribute_value_ids[k])==-1){
                                attribute_value_ids.push(product.attribute_value_ids[k]);
                            }
                        }
                        product['product_variant_count'] = templates[i].product_variant_count;
                        product['is_primary_variant'] = (j==0);
                        product.temp = templates[i].product_variant_count;
                    }
                }
                this.template_by_id[templates[i].id].attribute_value_ids = attribute_value_ids;
            }
        },

        add_product_attributes: function(product_attributes){
            for(var i=0 ; i < product_attributes.length; i++){
                // store Product Attributes
                this.product_attribute_by_id[product_attributes[i].id] = product_attributes[i];
            }
        },

        add_product_attribute_values: function(product_attribute_values){
            for(var i=0 ; i < product_attribute_values.length; i++){
                // store Product Attribute Values
                this.product_attribute_value_by_id[product_attribute_values[i].id] = product_attribute_values[i];
            }
        },

        search_product_name_description: function(category_id, query) {
            try {
                query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g, '.');
                query = query.replace(/ /g, '.+');
                var re = RegExp("([0-9]+):.*?" + query, "gi");
            } catch (e) {
                return [];
			}
            var results = [];
            for(var i = 0; i < this.limit; i++){
                var r = re.exec(this.product_search_string);
                //var r_desc = re.exec(this.product_search_string_desc);
                //console.log('Busqueda', r);
                if(r){
                    var id = Number(r[1]);
                    results.push(this.get_product_by_id(id));
                }else if (!r) {
                    var r_desc = re.exec(this.product_search_string_desc);
                    if (r_desc){
                        var id = Number(r_desc[1]);
                        results.push(this.get_product_by_id(id));
                    }
                }else{
                    break;
                }
            }
            /*for (var i = 0; i < this.limit; i++) {
                var r = re.exec(this.category_search_string[category_id]);
                if (r) {
                    var id = Number(r[1]);
                    results.push(this.get_product_by_id(id));
                } else {
                    break;
                }
            }*/
            return results;
        },
        _product_name_search_string: function(product){
            var str = product.display_name;
            str  = product.id + ':' + str.replace(/:/g,'') + '\n';
            return str;
        },
        // TODO: Habilitar para modificar el resto de busquedas
        /*_product_search_string: function(product){
            var str = product.display_name;
            if (product.barcode) {
                str += '|' + product.barcode;
            }
            if (product.default_code) {
                str += '|' + product.default_code;
            }
            if (product.description) {
                str += '|' + product.description;
            }
            if (product.description_sale) {
                str += '|' + product.description_sale;
            }
            if (product.product_brand_id[1]) {
                str += '|' + product.product_brand_id[1];
            }
            str  = product.id + ':' + str.replace(/:/g,'') + '\n';
            return str;
        },*/
	});
});