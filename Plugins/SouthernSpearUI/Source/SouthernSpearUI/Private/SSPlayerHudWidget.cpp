// Copyright Southern Spear. All Rights Reserved.

#include "SSPlayerHudWidget.h"

#include "Engine/World.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/CanvasPanelSlot.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "Components/Image.h"
#include "SSGlyphTextures.h"
#include "SSLocalHudState.h"
#include "SSUserPrefs.h"
#include "SSWidgetKit.h"

using namespace SSWidgetKit;

bool USSPlayerHudWidget::Initialize()
{
	if (!Super::Initialize())
	{
		return false;
	}
	if (!WidgetTree || WidgetTree->RootWidget)
	{
		return true;
	}
	UWidgetTree* T = WidgetTree;
	UCanvasPanel* Root = T->ConstructWidget<UCanvasPanel>();
	T->RootWidget = Root;

	// Hit flash: a clay wash over the whole screen, faded out in NativeTick.
	DamageFlash = Plate(T, SSPalette::Opfor500(0.f), FMargin(0.f));
	DamageFlash->SetVisibility(ESlateVisibility::HitTestInvisible);
	Fill(Root, DamageFlash);

	// Scope view: black either side of a square eyepiece (sized to the screen height in NativeTick), the mask
	// darkening the tube edge, and a fine black reticle: horizontal stadia with a centre gap, a post from below,
	// a small brass aim point. Shown only while aiming a magnified optic (USSLocalHudState::OpticMagnification).
	{
		UHorizontalBox* Row = T->ConstructWidget<UHorizontalBox>();
		ScopeOverlay = Row;
		Fill(Root, Row);
		AddH(Row, Plate(T, FLinearColor::Black, FMargin(0.f)), true, VAlign_Fill);
		ScopeEyepiece = T->ConstructWidget<USizeBox>();
		AddH(Row, ScopeEyepiece, false, VAlign_Center);
		AddH(Row, Plate(T, FLinearColor::Black, FMargin(0.f)), true, VAlign_Fill);
		UCanvasPanel* Eye = T->ConstructWidget<UCanvasPanel>();
		ScopeEyepiece->AddChild(Eye);
		UImage* Mask = T->ConstructWidget<UImage>();
		Mask->SetBrushFromTexture(SSGlyphTextures::ScopeMask(), /*bMatchSize=*/ false);
		UCanvasPanelSlot* MaskSlot = Eye->AddChildToCanvas(Mask);
		MaskSlot->SetAnchors(FAnchors(0.f, 0.f, 1.f, 1.f));
		MaskSlot->SetOffsets(FMargin(0.f));
		auto Line = [&](const FAnchors& Anchors, const FMargin& Offsets, const FLinearColor& Colour)
		{
			UBorder* B = Plate(T, Colour, FMargin(0.f));
			UCanvasPanelSlot* S = Eye->AddChildToCanvas(B);
			S->SetAnchors(Anchors);
			S->SetOffsets(Offsets);
		};
		const FLinearColor Ink(0.02f, 0.02f, 0.02f, 0.95f);
		Line(FAnchors(0.06f, 0.5f, 0.44f, 0.5f), FMargin(0.f, -1.f, 0.f, 1.f), Ink); // left stadia
		Line(FAnchors(0.56f, 0.5f, 0.94f, 0.5f), FMargin(0.f, -1.f, 0.f, 1.f), Ink); // right stadia
		Line(FAnchors(0.5f, 0.54f, 0.5f, 0.94f), FMargin(-1.5f, 0.f, 1.5f, 0.f), Ink); // post from below
		Line(FAnchors(0.5f, 0.5f), FMargin(-2.f, -2.f, 4.f, 4.f), SSPalette::Brass300()); // aim point
		Row->SetVisibility(ESlateVisibility::Collapsed);
	}

	// Hit direction: a clay arrow on a ring around the crosshair, pointing at the shooter.
	HitArrow = T->ConstructWidget<UImage>();
	HitArrow->SetBrushFromTexture(SSGlyphTextures::Triangle(), /*bMatchSize=*/ false);
	HitArrow->SetColorAndOpacity(SSPalette::Opfor500());
	HitArrow->SetVisibility(ESlateVisibility::Collapsed);
	HitArrow->SetRenderTransformPivot(FVector2D(0.5f, 0.5f));
	UCanvasPanelSlot* ArrowSlot = Root->AddChildToCanvas(HitArrow);
	ArrowSlot->SetAnchors(FAnchors(0.5f, 0.5f));
	ArrowSlot->SetAlignment(FVector2D(0.5f, 0.5f));
	ArrowSlot->SetSize(FVector2D(30.f, 22.f));

	// Health, bottom left: label, number, two-segment bar.
	UVerticalBox* Health = T->ConstructWidget<UVerticalBox>();
	HealthPanel = Health;
	Pin(Root, Health, FVector2D(0.f, 1.f), FVector2D(32.f, -32.f));
	AddV(Health, Rule(T, SSPalette::Brass500(), 2.f, 260.f));
	UBorder* HealthPlate = Plate(T, SSPalette::Ink900(0.82f), FMargin(14.f, 8.f, 14.f, 12.f));
	AddV(Health, HealthPlate);
	UVerticalBox* HealthBody = T->ConstructWidget<UVerticalBox>();
	HealthPlate->SetContent(HealthBody);
	UHorizontalBox* HealthRow = T->ConstructWidget<UHorizontalBox>();
	AddV(HealthBody, HealthRow);
	UTextBlock* HealthLabel = Text(T, 11, true, SSPalette::Sage400(), 200);
	HealthLabel->SetText(NSLOCTEXT("SSHud", "Health", "HEALTH"));
	AddH(HealthRow, HealthLabel, false, VAlign_Bottom)->SetPadding(FMargin(0.f, 0.f, 0.f, 4.f));
	AddH(HealthRow, T->ConstructWidget<USpacer>(), true);
	HealthText = Text(T, 26, true, SSPalette::Sand100());
	AddH(HealthRow, HealthText, false, VAlign_Bottom);
	USizeBox* BarSize = T->ConstructWidget<USizeBox>();
	BarSize->SetWidthOverride(232.f);
	BarSize->SetHeightOverride(6.f);
	AddV(HealthBody, BarSize, 6.f);
	UHorizontalBox* Bar = T->ConstructWidget<UHorizontalBox>();
	BarSize->AddChild(Bar);
	HealthFill = Plate(T, SSPalette::Sage200(), FMargin(0.f));
	HealthFillSlot = AddH(Bar, HealthFill, true, VAlign_Fill);
	HealthEmptySlot = AddH(Bar, Plate(T, SSPalette::Field700(), FMargin(0.f)), true, VAlign_Fill);

	// Ammunition, bottom right: weapon name, magazine / reserve.
	UVerticalBox* Ammo = T->ConstructWidget<UVerticalBox>();
	AmmoPanel = Ammo;
	Pin(Root, Ammo, FVector2D(1.f, 1.f), FVector2D(-32.f, -32.f));
	AddV(Ammo, Rule(T, SSPalette::Brass500(), 2.f, 240.f));
	UBorder* AmmoPlate = Plate(T, SSPalette::Ink900(0.82f), FMargin(14.f, 8.f, 14.f, 10.f));
	AddV(Ammo, AmmoPlate);
	UVerticalBox* AmmoBody = T->ConstructWidget<UVerticalBox>();
	AmmoPlate->SetContent(AmmoBody);
	WeaponText = Text(T, 12, true, SSPalette::Brass300(), 200);
	AddV(AmmoBody, WeaponText, 0.f, HAlign_Right);
	UHorizontalBox* Counts = T->ConstructWidget<UHorizontalBox>();
	AddV(AmmoBody, Counts, 2.f, HAlign_Right);
	MagazineText = Text(T, 34, true, SSPalette::Sand100());
	AddH(Counts, MagazineText, false, VAlign_Bottom);
	ReserveText = Text(T, 16, true, SSPalette::Sage400());
	AddH(Counts, ReserveText, false, VAlign_Bottom)->SetPadding(FMargin(8.f, 0.f, 0.f, 6.f));

	// Reload prompt under the crosshair.
	ReloadHint = Text(T, 13, true, SSPalette::Brass300(), 240);
	UCanvasPanelSlot* HintSlot = Root->AddChildToCanvas(ReloadHint);
	HintSlot->SetAnchors(FAnchors(0.5f, 0.5f));
	HintSlot->SetAlignment(FVector2D(0.5f, 0.f));
	HintSlot->SetPosition(FVector2D(0.f, 64.f));
	HintSlot->SetAutoSize(true);
	ReloadHint->SetVisibility(ESlateVisibility::Collapsed);

	// Frame rate counter (Settings > Interface), top left, mono-style digits.
	FpsText = Text(T, 12, true, SSPalette::Sage200(), 120);
	UCanvasPanelSlot* FpsSlot = Root->AddChildToCanvas(FpsText);
	FpsSlot->SetAnchors(FAnchors(0.f, 0.f));
	FpsSlot->SetPosition(FVector2D(16.f, 12.f));
	FpsSlot->SetAutoSize(true);
	FpsText->SetVisibility(ESlateVisibility::Collapsed);

	// Crosshair: four ticks and a centre dot on a fixed 80 px canvas.
	UCanvasPanel* Cross = T->ConstructWidget<UCanvasPanel>();
	Crosshair = Cross;
	UCanvasPanelSlot* CrossSlot = Root->AddChildToCanvas(Cross);
	CrossSlot->SetAnchors(FAnchors(0.5f, 0.5f));
	CrossSlot->SetAlignment(FVector2D(0.5f, 0.5f));
	CrossSlot->SetSize(FVector2D(80.f, 80.f));
	auto AddTick = [&](const FVector2D& Size)
	{
		UBorder* B = Plate(T, SSPalette::Sand100(0.9f), FMargin(0.f));
		UCanvasPanelSlot* S = Cross->AddChildToCanvas(B);
		S->SetSize(Size);
		S->SetAlignment(FVector2D(0.5f, 0.5f));
		S->SetPosition(FVector2D(40.f, 40.f));
		return B;
	};
	CrosshairTicks.Add(AddTick(FVector2D(2.f, 9.f)));  // up
	CrosshairTicks.Add(AddTick(FVector2D(2.f, 9.f)));  // down
	CrosshairTicks.Add(AddTick(FVector2D(9.f, 2.f)));  // left
	CrosshairTicks.Add(AddTick(FVector2D(9.f, 2.f)));  // right
	AddTick(FVector2D(2.f, 2.f));                      // centre dot
	return true;
}

void USSPlayerHudWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	if (FpsText)
	{
		// Smoothed over ~0.5 s; the preference is re-read twice a second.
		FpsAverage = FMath::Lerp(FpsAverage, InDeltaTime, FMath::Min(1.f, InDeltaTime * 4.f));
		FpsRefresh -= InDeltaTime;
		if (FpsRefresh <= 0.f)
		{
			FpsRefresh = 0.5f;
			const bool bShow = FSSUserPrefs::GetInt(FSSUserPrefs::ShowFps(), 0) != 0;
			FpsText->SetVisibility(bShow ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
			FpsText->SetText(FText::FromString(FString::Printf(TEXT("%d FPS  ·  %.1f MS"),
				FMath::RoundToInt(1.f / FMath::Max(FpsAverage, 0.0001f)), FpsAverage * 1000.f)));
		}
	}
	const USSLocalHudState* State = GetWorld() ? GetWorld()->GetSubsystem<USSLocalHudState>() : nullptr;
	if (!State || !HealthText)
	{
		return;
	}
	HealthPanel->SetVisibility(State->bHasPawn ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
	const bool bScoped = State->bHasPawn && State->bAiming && State->OpticMagnification > 1.f;
	ScopeOverlay->SetVisibility(bScoped ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
	if (bScoped)
	{
		// A round eyepiece as tall as the screen (the widget's local units, so DPI scaling is already applied).
		const float Height = MyGeometry.GetLocalSize().Y;
		ScopeEyepiece->SetWidthOverride(Height);
		ScopeEyepiece->SetHeightOverride(Height);
	}
	Crosshair->SetVisibility(State->bHasPawn && !State->bAiming ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
	AmmoPanel->SetVisibility(State->bHasPawn && State->Magazine >= 0 ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);

	const float Fraction = State->GetHealthFraction();
	const bool bLow = Fraction <= 0.3f;
	HealthText->SetText(FText::AsNumber(FMath::CeilToInt(State->Health)));
	HealthText->SetColorAndOpacity(bLow ? SSPalette::Opfor300() : SSPalette::Sand100());
	HealthFill->SetBrushColor(bLow ? SSPalette::Opfor300() : SSPalette::Sage200());
	FSlateChildSize FillSize(ESlateSizeRule::Fill), EmptySize(ESlateSizeRule::Fill);
	FillSize.Value = FMath::Max(Fraction, 0.001f);
	EmptySize.Value = FMath::Max(1.f - Fraction, 0.001f);
	HealthFillSlot->SetSize(FillSize);
	HealthEmptySlot->SetSize(EmptySize);

	// Clay flash when health drops, scaled by the size of the hit.
	if (State->bHasPawn && LastHealth > 0.f && State->Health < LastHealth && State->MaxHealth > 0.f)
	{
		FlashAlpha = FMath::Min(0.45f, FlashAlpha + 0.15f + (LastHealth - State->Health) / State->MaxHealth);
	}
	LastHealth = State->bHasPawn ? State->Health : -1.f;
	FlashAlpha = FMath::FInterpConstantTo(FlashAlpha, 0.f, InDeltaTime, 0.9f);
	DamageFlash->SetBrushColor(SSPalette::Opfor500(FlashAlpha));

	// Hit direction arrow: 1.5 s after a hit, placed by the shooter's bearing relative to the camera.
	const double Age = GetWorld() && State->LastHitTime >= 0.0 ? GetWorld()->GetTimeSeconds() - State->LastHitTime : 999.0;
	const APlayerController* PC = GetOwningPlayer();
	if (HitArrow && State->bHasPawn && Age < 1.5 && PC && PC->PlayerCameraManager)
	{
		const float Bearing = USSLocalHudState::HitBearing(PC->PlayerCameraManager->GetCameraLocation(),
			PC->PlayerCameraManager->GetCameraRotation().Yaw, State->LastHitFrom);
		const float Rad = FMath::DegreesToRadians(Bearing);
		Cast<UCanvasPanelSlot>(HitArrow->Slot)->SetPosition(FVector2D(FMath::Sin(Rad), -FMath::Cos(Rad)) * 150.f);
		HitArrow->SetRenderTransformAngle(Bearing);
		HitArrow->SetRenderOpacity(FMath::Clamp(1.f - static_cast<float>(Age) / 1.5f, 0.f, 1.f));
		HitArrow->SetVisibility(ESlateVisibility::HitTestInvisible);
	}
	else if (HitArrow)
	{
		HitArrow->SetVisibility(ESlateVisibility::Collapsed);
	}

	MagazineText->SetText(FText::AsNumber(FMath::Max(State->Magazine, 0)));
	const bool bLowAmmo = State->MagazineSize > 0 && State->Magazine * 4 <= State->MagazineSize;
	MagazineText->SetColorAndOpacity(bLowAmmo ? SSPalette::Opfor300() : SSPalette::Sand100());
	Elapsed += InDeltaTime;
	const bool bEmpty = State->Magazine == 0 && State->Reserve == 0;
	const bool bHint = State->bHasPawn && State->Magazine >= 0 && (bLowAmmo || bEmpty);
	ReloadHint->SetVisibility(bHint ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
	if (bHint)
	{
		ReloadHint->SetText(bEmpty ? NSLOCTEXT("SSHud", "NoAmmo", "NO AMMUNITION") : NSLOCTEXT("SSHud", "Reload", "R  ·  RELOAD"));
		ReloadHint->SetRenderOpacity(0.55f + 0.45f * FMath::Abs(FMath::Sin(Elapsed * 3.f)));
	}
	ReserveText->SetText(FText::Format(NSLOCTEXT("SSHud", "Reserve", "/ {0}"), FText::AsNumber(FMath::Max(State->Reserve, 0))));
	WeaponText->SetText(State->WeaponName.ToUpper());

	// Crosshair opens with movement speed.
	const APawn* Pawn = GetOwningPlayerPawn();
	const float Speed = Pawn ? Pawn->GetVelocity().Size2D() : 0.f;
	Spread = FMath::FInterpTo(Spread, 10.f + FMath::Clamp(Speed / 600.f, 0.f, 1.f) * 16.f, InDeltaTime, 10.f);
	const FVector2D Centre(40.f, 40.f);
	const FVector2D Offsets[] = { {0.f, -Spread}, {0.f, Spread}, {-Spread, 0.f}, {Spread, 0.f} };
	for (int32 Index = 0; Index < CrosshairTicks.Num(); ++Index)
	{
		Cast<UCanvasPanelSlot>(CrosshairTicks[Index]->Slot)->SetPosition(Centre + Offsets[Index]);
	}
}
