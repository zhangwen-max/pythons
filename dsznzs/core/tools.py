from __future__ import annotations


ORDER_STATUS = {
    "123": "订单 123 已出库，当前在运输中，预计 3 天内送达。",
    "888": "订单 888 已签收，签收时间为昨天 18:20。",
}

RETURN_POLICY = (
    "退货退款流程：1. 在订单页提交售后申请；2. 选择退货原因并上传凭证；"
    "3. 平台审核通过后寄回商品；4. 仓库验收后原路退款。签收 7 天内通常可申请。"
)


def execute_business_tool(intent: str, slots: dict, user_input: str) -> str:
    if intent == "track_shipping":
        order_id = str(slots.get("order_id") or "")
        if not order_id:
            return "缺少订单号，无法查询物流。"
        return ORDER_STATUS.get(order_id, f"没有查到订单 {order_id} 的物流记录，请确认订单号。")
    if intent == "change_address":
        order_id = str(slots.get("order_id") or "")
        if not order_id:
            return "改地址需要订单号和新地址。"
        return f"订单 {order_id} 的改地址申请已记录；若订单已发货，需要快递侧确认是否还能修改。"
    if intent == "return_refund":
        return RETURN_POLICY
    if intent == "complaint":
        return "投诉已进入受理流程，请提供订单号、问题描述和相关凭证，客服将在 48 小时内跟进。"
    if intent == "product_consult":
        return "商品咨询建议：请说明预算、用途、品牌偏好、尺码或颜色要求，我会按需求推荐。"
    return ""

