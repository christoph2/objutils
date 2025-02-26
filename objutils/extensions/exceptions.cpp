
#include "exceptions.hpp"

RuntimeException::RuntimeException(std::string msg) : _message(std::move(msg)) {
}

const char *RuntimeException::what() const noexcept {
    return _message.c_str();
}

InvalidRecordTypeError::~InvalidRecordTypeError() {
}

InvalidRecordLengthError::~InvalidRecordLengthError() {
}

InvalidRecordChecksumError::~InvalidRecordChecksumError() {
}

AddressRangeToLargeError::~AddressRangeToLargeError() {
}
