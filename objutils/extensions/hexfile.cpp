
#include <any>
#include <map>
#include <regex>
#include <iostream>
#include <string>
#include <sstream>
#include <vector>
#include <cstdint>


#include "exceptions.hpp"

constexpr auto SIXTEEN_BITS = 0;
constexpr auto TWENTY_BITS = 1;
constexpr auto TWENTYFOUR_BITS = 2;
constexpr auto THIRTYTWO_BITS = 3;

constexpr auto START = 0;
constexpr auto LENGTH = 1;
constexpr auto TYPE = 2;
constexpr auto ADDRESS = 3;
constexpr auto DATA = 4;
constexpr auto UNPARSED = 5;
constexpr auto CHECKSUM = 6;
constexpr auto ADDR_CHECKSUM = 7;

constexpr auto TYPE_FROM_RECORD = 0;

static const auto LENGTH_EXPR = R"""(\(?<length>[0-9a-zA-Z])""";
static const auto TYPE_EXPR = R"""(\(?<type>\d\)""";
static const auto ADDRESS_EXPR = R"""(\(?<address>[0-9a-zA-Z])""";
static const auto DATA_EXPR = R"""(\(?<chunk>[0-9a-zA-Z]+)""";
static const auto CHECKSUM_EXPR = R"""(\(?<checksum>[0-9a-zA-Z])""";
static const auto ADDR_CHECKSUM_EXPR = R"""(\(?<addrChecksum>[0-9a-zA-Z])""";

const auto xxc = 'L';

static const std::map<const char, const std::string> MAP_CHAR_TO_GROUP = {
    {'L', LENGTH_EXPR},
    {'T', TYPE_EXPR},
    {'A', ADDRESS_EXPR},
    {'D', DATA_EXPR},
    {'C', CHECKSUM_EXPR},
    {'B', ADDR_CHECKSUM_EXPR},
};

struct MetaRecord {
    std::any format_type;
    std::uint64_t address;
    std::vector<std::byte> chunk;
};


class FormatParser {
public:
    explicit FormatParser(const std::string& format, const std::string& data_separator= " ") : m_format(format), m_data_separator(data_separator) {
        if (m_format.empty()) {
            throw std::invalid_argument("Format cannot be empty");
        }
    }

    void parse() const noexcept {
        std::string group{};
        std::string group_expr{};
        std::vector<std::string> translated_format_expr{};
        char previous_ch = '\0';

        for (char ch : m_format) {  // Group format-type characters.
            if (ch != previous_ch) {
                if (!group.empty()) {
                    group_expr = translate_format(group);
                    translated_format_expr.emplace_back(group_expr);
                    std::cout << "Group expression: " << group_expr << std::endl;
                    group = "";
                }
            }
            group += ch;
            previous_ch = ch;
        }
        if (!group.empty()) {
            group_expr = translate_format(group);
            translated_format_expr.emplace_back(group_expr);
            std::cout << "Group expression: " << group_expr << std::endl;
        }
        // translated_format_expr.emplace_back("\\(?P<junk>.*?\\)$");
        std::string resulting_expr{"^"};
        for (const auto& expr : translated_format_expr) {
            resulting_expr += expr;
        }
        std::cout << "Tfe: " << resulting_expr << std::endl;
        const std::regex regx {resulting_expr, std::regex_constants::ECMAScript};

        std::smatch match;
        std::string input{ "11 1234:56 5667  " };
        // LL AAAA:DD CCCC
        auto res = std::regex_search(input, match, regx);
        std::cout << "match? " << res << std::endl;
    }

    std::string translate_format(const std::string& group) const noexcept {
        auto type_code = group[0];
        auto length = std::size(group);
        auto group_number = MAP_CHAR_TO_GROUP.find(type_code);
        auto found = MAP_CHAR_TO_GROUP.contains(type_code);
        std::string expr{};

        if (found) {
            expr = group_number->second;
            if (type_code != 'D')  {
                // Everything but DATA blocks has a specific length.
                expr = expr + "{" + std::to_string(length) + "}\\)";
            } else {
                expr = expr + "\\)";
            }
        } else {
            if (type_code == ' ') {
                expr = "\\s{" + std::to_string(length) + "}";
            } else {
                expr = std::string(length, type_code);
                std::cout << "\tSpecial " << int(type_code)  << "'" << expr << "'" << std::endl;
            }
        }
        return expr;
    }

    #if 0
    def translateFormat(self, group):
        group_number = MAP_CHAR_TO_GROUP.get(group[0])
        length = len(group)
        if group_number is None:  # Handle invariants (i.e. fixed chars).
            if group[0] == " ":
                expr = rf"\s{{{length!s}}}"
            else:
                expr = group[0] * length
        else:
            expr = MAP_GROUP_TO_REGEX.get(group_number)
            if group_number == START:
                expr = expr % (self.startSign,)
            elif group_number == DATA:
                r"(?P<chunk>[0-9a-zA-Z]*)"
                if self.data_separator is not None:
                    expr = rf"(?P<chunk>[0-9a-zA-Z{self.data_separator!s}]*)"
                else:
                    pass
            elif group_number == UNPARSED:
                # print expr
                pass
            else:
                expr = expr % (length,)
        self.translated_format.append((group_number, length, expr))    #endif
#endif

private:
    std::string m_format;
    std::string m_data_separator;
};


int main() {
    std::string input = "L:16,T:0x1,A:0x1000,D:ABCD,U:EFGH,C:1234,B:5678";

    const std::regex RT {R"""(\(?<len>[0-9a-zA-Z]{2}\))"""};

    auto STS = std::string(100, '=');
    std::cout << STS << std::endl;

    auto FMT = "LL AAAA:DD CCCC";
    auto fmp = FormatParser{FMT};
    fmp.parse();

    //auto res = ctre::match<PAT_FLOAT>( "10.45633");
    // auto res = std::regex::match<DATA_RE>( "0123563534636");
 //   auto ma = res.matched() ;
 //   std::cout << ma << std::endl;

    //std::smatch match;
    //std::regex_match(input, match, ctll::make_matcher(std::regex{ R"(L:(?P<length>[0-9a-fA-F]+),T:(?P<type>[0-9a-fA-F]+),A:(?P<address>[0-9a-fA-F]+),D:(?P<chunk>[0-9a-fA-F]+),U:(?P<unparsed>[0-9a-fA-F]+),C:(?P<checksum>[0-9a-fA-F]+),B:(?P<addrChecksum>[0-9a-fA-F]+))" }));

}
