from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین بروزرسانی",
    )

    class Meta:
        abstract = True


def generate_unique_slug(model, *, text, slug_field="slug", pk=None):
    """تولید اسلاگ یکتا با پشتیبانی از حروف فارسی."""
    base = slugify(text, allow_unicode=True) or "item"
    slug = base
    counter = 2

    queryset = model.objects.all()
    if pk:
        queryset = queryset.exclude(pk=pk)

    while queryset.filter(**{slug_field: slug}).exists():
        slug = f"{base}-{counter}"
        counter += 1

    return slug


class Category(models.Model):
    name = models.CharField(
        max_length=120,
        unique=True,
        verbose_name="نام دسته‌بندی",
    )
    slug = models.SlugField(
        max_length=140,
        unique=True,
        allow_unicode=True,
        verbose_name="اسلاگ",
    )
    description = models.TextField(
        blank=True,
        verbose_name="توضیحات",
    )
    image = models.ImageField(
        upload_to="categories/",
        blank=True,
        null=True,
        verbose_name="تصویر",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال",
    )

    class Meta:
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"
        ordering = ("name",)
        indexes = [
            models.Index(fields=("is_active", "slug")),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(
                Category, text=self.name, pk=self.pk,
            )
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("shop:category", args=[self.slug])


class Brand(models.Model):
    name = models.CharField(
        max_length=120,
        unique=True,
        verbose_name="نام برند",
    )
    slug = models.SlugField(
        max_length=140,
        unique=True,
        allow_unicode=True,
        verbose_name="اسلاگ",
    )
    logo = models.ImageField(
        upload_to="brands/",
        blank=True,
        null=True,
        verbose_name="لوگو",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال",
    )

    class Meta:
        verbose_name = "برند"
        verbose_name_plural = "برندها"
        ordering = ("name",)
        indexes = [
            models.Index(fields=("is_active", "slug")),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(
                Brand, text=self.name, pk=self.pk,
            )
        super().save(*args, **kwargs)


class Product(TimeStampedModel):
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name="دسته‌بندی",
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        verbose_name="برند",
    )

    name = models.CharField(
        max_length=255,
        verbose_name="نام محصول",
    )
    slug = models.SlugField(
        max_length=280,
        unique=True,
        allow_unicode=True,
        verbose_name="اسلاگ",
    )
    sku = models.CharField(
        max_length=80,
        unique=True,
        verbose_name="کد محصول",
    )

    short_description = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="توضیح کوتاه",
    )
    description = models.TextField(
        blank=True,
        verbose_name="توضیحات",
    )

    price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="قیمت",
    )
    discount_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="قیمت تخفیف",
    )

    stock = models.PositiveIntegerField(
        default=0,
        verbose_name="موجودی",
    )

    is_available = models.BooleanField(
        default=True,
        verbose_name="قابل فروش",
    )
    is_featured = models.BooleanField(
        default=False,
        verbose_name="محصول ویژه",
    )

    meta_title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="عنوان SEO",
    )
    meta_description = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="توضیحات SEO",
    )

    class Meta:
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("is_available", "category")),
            models.Index(fields=("is_available", "brand")),
            models.Index(fields=("is_featured", "is_available")),
            models.Index(fields=("-created_at",)),
        ]

    def __str__(self):
        return self.name

    @property
    def final_price(self) -> Decimal:
        if (
                self.discount_price is not None
                and self.discount_price < self.price
        ):
            return self.discount_price
        return self.price

    @property
    def has_discount(self) -> bool:
        return self.discount_price is not None and self.discount_price < self.price

    @property
    def discount_percentage(self) -> int:
        if not self.has_discount or not self.price:
            return 0
        return round(
            (self.price - self.final_price) * Decimal("100") / self.price
        )

    @property
    def in_stock(self) -> bool:
        return self.is_available and self.stock > 0

    @property
    def primary_image(self):
        """تصویر اصلی؛ در نبود آن اولین تصویر."""
        for image in self.images.all():
            if image.is_primary:
                return image
        return self.images.first()

    @property
    def seo_title(self) -> str:
        return self.meta_title or self.name

    @property
    def seo_description(self) -> str:
        return self.meta_description or self.short_description

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(
                Product, text=self.name, pk=self.pk,
            )

        if (
                self.discount_price is not None
                and self.discount_price >= self.price
        ):
            self.discount_price = None

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("products:detail", args=[self.slug])


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="محصول",
    )
    image = models.ImageField(
        upload_to="products/%Y/%m/",
        verbose_name="تصویر",
    )
    alt_text = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="متن جایگزین",
    )
    is_primary = models.BooleanField(
        default=False,
        verbose_name="تصویر اصلی",
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name="ترتیب",
    )

    class Meta:
        verbose_name = "تصویر محصول"
        verbose_name_plural = "تصاویر محصولات"
        ordering = ("sort_order", "id")
        indexes = [
            models.Index(fields=("product", "is_primary")),
        ]

    def __str__(self):
        return f"{self.product.name} - تصویر {self.pk}"

    def save(self, *args, **kwargs):
        if not self.alt_text:
            self.alt_text = self.product.name

        if self.is_primary:
            ProductImage.objects.filter(
                product=self.product,
                is_primary=True,
            ).exclude(pk=self.pk).update(is_primary=False)

        super().save(*args, **kwargs)


class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants",
        verbose_name="محصول",
    )
    name = models.CharField(
        max_length=150,
        verbose_name="نام تنوع",
    )
    sku = models.CharField(
        max_length=80,
        unique=True,
        verbose_name="کد تنوع",
    )
    price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="قیمت",
    )
    stock = models.PositiveIntegerField(
        default=0,
        verbose_name="موجودی",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال",
    )

    class Meta:
        verbose_name = "تنوع محصول"
        verbose_name_plural = "تنوع‌های محصول"
        ordering = ("id",)
        constraints = [
            models.UniqueConstraint(
                fields=("product", "name"),
                name="unique_variant_name_per_product",
            ),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    @property
    def final_price(self) -> Decimal:
        return (
            self.price
            if self.price is not None
            else self.product.final_price
        )

    @property
    def in_stock(self) -> bool:
        return self.is_active and self.product.is_available and self.stock > 0


class ProductAttribute(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="attributes",
        verbose_name="محصول",
    )
    name = models.CharField(
        max_length=100,
        verbose_name="ویژگی",
    )
    value = models.CharField(
        max_length=255,
        verbose_name="مقدار",
    )

    class Meta:
        verbose_name = "ویژگی محصول"
        verbose_name_plural = "ویژگی‌های محصولات"
        ordering = ("id",)
        constraints = [
            models.UniqueConstraint(
                fields=("product", "name"),
                name="unique_attribute_name_per_product",
            ),
        ]

    def __str__(self):
        return f"{self.name}: {self.value}"
