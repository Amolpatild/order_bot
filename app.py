from flask import Flask, request, jsonify,render_template
import traceback
import os
import db_helper
import generic_helper
from word2number import w2n



app = Flask(__name__)
cf_port = os.getenv("PORT")

inplace_orders = {}

@app.route("/", methods=["POST"])

def handle_webhook():
    
    payload = request.json
    print("Received payload:", payload)  # Debug statement

    intent = payload['nlp']['intents'][0]['slug']
    parameter = payload['nlp']
    conversation_id = payload['conversation']['conversation_id']
    

    intent_handler_dict = {
        'order_add_context': add_to_order,
        'order_remove_context': remove_from_order,
        'order_complete': complete_order,
        'track_order_context': track_order
    }

        
    return intent_handler_dict[intent](parameter,conversation_id)

def home():
    return render_template('app.html')
    

def add_to_order(parameter, conversation_id):
    quantity = parameter['entities']['number']
    mixed_list = [i['scalar'] for i in quantity]
    food_items = parameter['entities']['food_items']
    food_it = [i['value'] for i in food_items]   
    print(f'here ============{food_it}')
    print(f'here ============{mixed_list}')
    
    
    converted_list = []
    
    for item in mixed_list:
        if isinstance(item, str):  # Check if the item is a string (word)
            try:
                numerical_value = w2n.word_to_num(item)
                converted_list.append(numerical_value)
            except ValueError:
                print(f"Skipping '{item}' as it couldn't be converted.")
        else:
            converted_list.append(item)  # Keep integers unchanged

    print("Original list:", mixed_list)
    print("Converted list:", converted_list)


    if len(converted_list) != len(food_it):
        fullfilment_text = "Please provide mandidate inormation"
    
    else:
        new_food_dict = dict(zip(food_it,converted_list))

        if conversation_id in inplace_orders:
            current_food_dict = inplace_orders[conversation_id]
            current_food_dict.update(new_food_dict)
            inplace_orders[conversation_id] = current_food_dict
        else:
            inplace_orders[conversation_id] = new_food_dict
        
        print(f"***************{inplace_orders}***************")
        
        order_str = generic_helper.get_str_from_food_dict(inplace_orders[conversation_id])
        print(f'================{order_str}')
        fullfilment_text = f"So far you have: {order_str}. Do you need anything else?"

    response = {
                "replies": [
                    {
                        "type": "text",
                        "content": fullfilment_text
                    }
                ]
            }
   
    return jsonify(response)  
    
def remove_from_order(parameter, conversation_id):
    if conversation_id not in inplace_orders:
        
        response = {
        "replies": [
            {
                "type": "text",
                "content": "I'm having a trouble finding your order. Sorry! Can you place a new order please?"
            }
        ]
    }
        return jsonify(response)
    else:
        current_order = inplace_orders[conversation_id]
        food_itms = parameter['entities']['food_items']
        food_it = [i['value'] for i in food_itms]

        item_remvoed = []
        not_such_item = []
        for item in food_it:
             if item not in current_order:
                  not_such_item.append(item)
             else:
                  item_remvoed.append(item)
                  del current_order[item]

        if len(item_remvoed) > 0:
            fulfillment_text = f'Removed {",".join(item_remvoed)} from your order!'
        
        if len(not_such_item) > 0:
            fulfillment_text = f' Your current order does not have {",".join(not_such_item)}'

    if len(current_order.keys()) == 0:
        fulfillment_text += " Your order is empty!"
    else:
        order_str = generic_helper.get_str_from_food_dict(current_order)
        fulfillment_text += f" Here is what is left in your order: {order_str}"
          
    response = {
            "replies": [
                {
                    "type": "text",
                    "content": fulfillment_text
                }
            ]
        }
    return jsonify(response)  
      
def complete_order(parameter, conversation_id):
    if conversation_id not in inplace_orders:
        fulfillment_text = "I am finding troublshoot in your order, Sorry! can you place a new oder please? "
    
    else:
        order = inplace_orders[conversation_id]
        order_id = save_to_db(order)

        if order_id == -1:
                fulfillment_text = "Sorry, I couldn't process your order due to a backend error. " \
                "Please place a new order again"
        else:
            order_total = db_helper.get_total_order_price(order_id)
            fulfillment_text = f"Awesome. We have placed your order. " \
                           f"Here is your order id # {order_id}. " \
                           f"Your order total is {order_total} which you can pay at the time of delivery!"
        
        del inplace_orders[conversation_id]

        response = {
                "replies": [
                    {
                        "type": "text",
                        "content": fulfillment_text
                    }
                ]
            }
    return jsonify(response)


def save_to_db(order):

    next_order_id = db_helper.get_next_order_id() 
    for food_item,quantity in order.items():
        print(food_item,quantity)
        rcode = db_helper.insert_order_item(food_item, quantity,next_order_id)
        if rcode == -1:
             return -1
    
    db_helper.insert_order_tracking(next_order_id,"in progress")
        

    return next_order_id

    
def track_order(parameter,conversation_id):
    order_id = int(parameter['entities']['number'][0]['scalar'])
    
    order_status = db_helper.get_name_from_database(order_id)
    print(f'................order_status')
    if order_status:
        fulfilment = f"The order status for order id : {order_id} is {order_status} "
        response = {
                "replies": [
                    {
                        "type": "text",
                        "content": fulfilment
                    }
                ]
            }
    else:
        fulfilment = f"order id {order_id} not found"
        response = {
                "replies": [
                    {
                        "type": "text",
                        "content": fulfilment
                    }
                ]
            }
    return jsonify(response)




if __name__ == '__main__':
	if cf_port is None:
		app.run(host='0.0.0.0', port=5000, debug=True)
	else:
		app.run(host='0.0.0.0', port=int(cf_port), debug=True)