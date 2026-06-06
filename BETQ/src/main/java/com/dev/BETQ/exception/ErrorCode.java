package com.dev.BETQ.exception;
import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
public enum ErrorCode {

    // ================= AUTH =================
    USER_EXISTED(409, "USER_EXISTED", "SĐT đã tồn tại"),
    USER_NOT_FOUND(404, "USER_NOT_FOUND", "Tài khoản không tồn tại"),
    UNAUTHORIZED(401, "UNAUTHORIZED", "Thông tin đăng nhập sai"),
    ACCOUNT_LOCKED(423, "ACCOUNT_LOCKED", "Tài khoản bạn đã bị khóa"),
    USER_ALREADY_LOCKED(409, "USER_ALREADY_LOCKED", "Tài khoản đã khóa rồi"),
    USER_ALREADY_ACTIVE(409, "USER_ALREADY_ACTIVE", "Tài khoản này đã mở rồi"),

    // ================= PASSWORD =================
    PASSWORD_WRONG(400, "PASSWORD_WRONG", "Mật khẩu hiện tại sai"),
    PASSWORD_SAME_AS_OLD(400, "PASSWORD_SAME_AS_OLD", "Mật khẩu phải khác mật khẩu hiện tại"),

    TOKEN_INVALID(403,"TOKEN_INVALID","Token không hợp lệ"),
    TOKEN_EXPIRED(403,"TOKEN_EXPIRED","Token hết hạn"),
    TOKEN_NOT_FOUND(404,"TOKEN_NOT_FOUND","Không tìm thấy token"),
    TOKEN_REVOKED(403,"TOKEN_REVOKED","Token đã thu hồi"),
    REVIEW_NOTFOUND(404,"REVIEW_NOTFOUND","KHÔNG TỒN TẠI REVIEW NÀY");

    private final int status;
    private final String code;
    private final String message;
}