import mysql.connector

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Test@1234",
    database="test"
)


def insert_order_item(food_item, quantity, order_id):
    try:
        cursor = connection.cursor()

        # Calling the stored procedure
        cursor.callproc('pandeyji_eatery.insert_order_item', (food_item, quantity, order_id))

        # Committing the changes
        connection.commit()

        # Closing the cursor
        cursor.close()

        print("Order item inserted successfully!")

        return 1

    except mysql.connector.Error as err:
        print(f"Error inserting order item: {err}")

        # Rollback changes if necessary
        connection.rollback()

        return -1
    except Exception as e:
        print(f"An error occurred: {e}")
        # Rollback changes if necessary
        connection.rollback()

        return -1
    

def get_name_from_database(order_id):
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Test@1234",
            database="test"
        )
        cursor = connection.cursor()
        query = f"SELECT status FROM pandeyji_eatery.order_tracking WHERE order_id = {order_id}"
        

        cursor.execute(query)
        row = cursor.fetchone()


        cursor.close()
        connection.close()

        if row:
            return row[0]
        else:
            return None
    except mysql.connector.Error as error:
        print("Error while connecting to the database:", error)
        return None



def get_next_order_id():
    cursor = connection.cursor()

    # Executing the SQL query to get the next available order_id
    query = "SELECT MAX(order_id) FROM pandeyji_eatery.orders"
    cursor.execute(query)

    # Fetching the result
    result = cursor.fetchone()[0]
    print(f'====> {result}')

    # Closing the cursor
    cursor.close()

    # Returning the next available order_id
    if result is None:
        return 1
    else:
        return result + 1
    
def insert_order_tracking(order_id, status):
    cursor = connection.cursor()

    # Inserting the record into the order_tracking table
    insert_query = "INSERT INTO pandeyji_eatery.order_tracking (order_id, status) VALUES (%s, %s)"
    cursor.execute(insert_query, (order_id, status))

    # Committing the changes
    connection.commit()

    # Closing the cursor
    cursor.close()
    

def get_total_order_price(order_id):
    cursor = connection.cursor()

    # Executing the SQL query to get the total order price
    query = f"SELECT pandeyji_eatery.get_total_order_price({order_id})"
    cursor.execute(query)

    # Fetching the result
    result = cursor.fetchone()[0]
    print(f"final price {result}")

    # Closing the cursor
    cursor.close()

    return result


if __name__ == "__main__":
    print(get_total_order_price(100))
    # # insert_order_item('Samosa', 3, 99)
    # insert_order_item('masala dosa', 1, 100)
    # insert_order_tracking(100, "in progress")
    # print(get_next_order_id())
