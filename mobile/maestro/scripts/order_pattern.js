// The order's row in My orders starts with "Order #<n>" and may run on over
// several lines in one accessibility label; (?s) lets ".*" cross them.
output.orderPattern = "(?s)" + maestro.copiedText.replace("#", "\\#") + "(\\n.*)?";
