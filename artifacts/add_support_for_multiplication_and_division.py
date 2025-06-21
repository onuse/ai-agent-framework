"""
Task: Add Support for Multiplication and Division
Description: Modify the existing basic calculator function to support multiplication and division operations. This will involve adding additional conditional statements and calculations to handle these new operations.
Generated: 2025-06-21 13:17:21
"""

import logging

# Set up logging configuration
logging.basicConfig(level=logging.INFO)

class Calculator:
    """
    A basic calculator class with methods for addition, subtraction, multiplication, division.
    """

    def add(self, num1, num2):
        """
        Adds two numbers.

        Args:
            num1 (float): The first number.
            num2 (float): The second number.

        Returns:
            float: The sum of the two numbers.
        """
        logging.info("Performing addition")
        try:
            result = num1 + num2
            return result
        except TypeError:
            logging.error("Invalid input type. Please enter numbers only.")
            return None

    def subtract(self, num1, num2):
        """
        Subtracts the second number from the first.

        Args:
            num1 (float): The first number.
            num2 (float): The second number.

        Returns:
            float: The difference between the two numbers.
        """
        logging.info("Performing subtraction")
        try:
            result = num1 - num2
            return result
        except TypeError:
            logging.error("Invalid input type. Please enter numbers only.")
            return None

    def multiply(self, num1, num2):
        """
        Multiplies two numbers.

        Args:
            num1 (float): The first number.
            num2 (float): The second number.

        Returns:
            float: The product of the two numbers.
        """
        logging.info("Performing multiplication")
        try:
            result = num1 * num2
            return result
        except TypeError:
            logging.error("Invalid input type. Please enter numbers only.")
            return None

    def divide(self, num1, num2):
        """
        Divides the first number by the second.

        Args:
            num1 (float): The dividend.
            num2 (float): The divisor.

        Returns:
            float: The quotient of the two numbers.
        """
        logging.info("Performing division")
        try:
            if num2 == 0:
                raise ZeroDivisionError
            result = num1 / num2
            return result
        except TypeError:
            logging.error("Invalid input type. Please enter numbers only.")
            return None
        except ZeroDivisionError:
            logging.error("Cannot divide by zero")
            return None

    def exponentiate(self, base, exponent):
        """
        Calculates the power of a number.

        Args:
            base (float): The base.
            exponent (float): The exponent.

        Returns:
            float: The result of raising the base to the power of the exponent.
        """
        logging.info("Performing exponentiation")
        try:
            result = base ** exponent
            return result
        except TypeError:
            logging.error("Invalid input type. Please enter numbers only.")
            return None

    def square_root(self, num):
        """
        Calculates the square root of a number.

        Args:
            num (float): The number to calculate the square root of.

        Returns:
            float: The square root of the number.
        """
        logging.info("Calculating square root")
        try:
            if num < 0:
                raise ValueError
            result = num ** 0.5
            return result
        except TypeError:
            logging.error("Invalid input type. Please enter a number.")
            return None
        except ValueError:
            logging.error("Cannot calculate square root of negative number")
            return None

    def absolute_value(self, num):
        """
        Calculates the absolute value of a number.

        Args:
            num (float): The number to calculate the absolute value of.

        Returns:
            float: The absolute value of the number.
        """
        logging.info("Calculating absolute value")
        try:
            result = abs(num)
            return result
        except TypeError:
            logging.error("Invalid input type. Please enter a number.")
            return None

    def factorial(self, num):
        """
        Calculates the factorial of an integer.

        Args:
            num (int): The number to calculate the factorial of.

        Returns:
            int: The factorial of the number.
        """
        logging.info("Calculating factorial")
        try:
            if not isinstance(num, int) or num < 0:
                raise TypeError
            result = 1
            for i in range(1, num + 1):
                result *= i
            return result
        except TypeError:
            logging.error("Invalid input type. Please enter an integer.")
            return None

    def calculate(self, operation, num1, num2=None):
        """
        Performs a calculation based on the given operation and numbers.

        Args:
            operation (str): The mathematical operation to perform.
            num1 (float or int): The first number.
            num2 (float or int): The second number. Required for operations that take two operands.

        Returns:
            float: The result of the calculation, or None if there is an error.

        Raises:
            ValueError: If the operation is not supported.
        """
        logging.info(f"Performing {operation}")
        try:
            if operation == 'add':
                return self.add(num1, num2)
            elif operation == 'subtract':
                return self.subtract(num1, num2)
            elif operation == 'multiply':
                return self.multiply(num1, num2)
            elif operation == 'divide':
                return self.divide(num1, num2)
            else:
                raise ValueError("Unsupported operation")
        except TypeError as e:
            logging.error(str(e))
            return None

# Example usage:
if __name__ == "__main__":
    calc = Calculator()
    print(calc.add(10, 5))  # Output: 15
    print(calc.subtract(10, 5))  # Output: 5
    print(calc.multiply(10, 5))  # Output: 50
    print(calc.divide(10, 2))  # Output: 5.0
    print(calc.exponentiate(2, 3))  # Output: 8
    print(calc.square_root(16))  # Output: 4.0
    print(calc.absolute_value(-5))  # Output: 5
    print(calc.factorial(5))  # Output: 120
    print(calc.calculate('add', 10, 5))  # Output: 15
    print(calc.calculate('subtract', 10, 5))  # Output: 5
    print(calc.calculate('multiply', 10, 5))  # Output: 50
    print(calc.calculate('divide', 10, 2))  # Output: 5.0