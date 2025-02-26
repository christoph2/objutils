
#if !defined(__EXCEPTIONS_HPP)
    #define __EXCEPTIONS_HPP

    #include <stdexcept>
    #include <string>

class RuntimeException : public std::exception {
   public:

    explicit RuntimeException(std::string msg = "");

    const char* what() const noexcept override;

   private:

    std::string _message;
};


class InvalidRecordTypeError : public RuntimeException {
   public:

    explicit InvalidRecordTypeError(const std::string& msg = "") : RuntimeException(msg) {
    }

    InvalidRecordTypeError(InvalidRecordTypeError const &) = default;
    ~InvalidRecordTypeError() override;
    InvalidRecordTypeError& operator=(InvalidRecordTypeError const &) = default;
};

class InvalidRecordLengthError : public RuntimeException {
   public:

    explicit InvalidRecordLengthError(const std::string& msg = "") : RuntimeException(msg) {
    }

    InvalidRecordLengthError(InvalidRecordLengthError const &) = default;
    ~InvalidRecordLengthError() override;
    InvalidRecordLengthError& operator=(InvalidRecordLengthError const &) = default;
};

class InvalidRecordChecksumError : public RuntimeException {
   public:

    InvalidRecordChecksumError(InvalidRecordChecksumError const &) = default;

    explicit InvalidRecordChecksumError(const std::string& msg = "") : RuntimeException(msg) {
    }

    ~InvalidRecordChecksumError() override;
    InvalidRecordChecksumError& operator=(InvalidRecordChecksumError const &) = default;
};

class AddressRangeToLargeError : public RuntimeException {
   public:

    explicit AddressRangeToLargeError(const std::string& msg = "") : RuntimeException(msg) {
    }

    AddressRangeToLargeError(AddressRangeToLargeError const &) = default;
    ~AddressRangeToLargeError() override;
    AddressRangeToLargeError& operator=(AddressRangeToLargeError const &) = default;
};

#endif  // __EXCEPTIONS_HPP
