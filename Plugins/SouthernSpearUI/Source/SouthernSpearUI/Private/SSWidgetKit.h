// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/Image.h"
#include "Components/SizeBox.h"
#include "Components/Spacer.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "SSPalette.h"
#include "Styling/CoreStyle.h"

/** Small helpers shared by the C++-built Southern Spear widgets. */
namespace SSWidgetKit
{
	inline UTextBlock* Text(UWidgetTree* Tree, int32 Size, bool bBold, const FLinearColor& Colour, int32 LetterSpacing = 0)
	{
		UTextBlock* T = Tree->ConstructWidget<UTextBlock>();
		FSlateFontInfo Font = FCoreStyle::GetDefaultFontStyle(bBold ? "Bold" : "Regular", Size);
		Font.LetterSpacing = LetterSpacing;
		T->SetFont(Font);
		T->SetColorAndOpacity(Colour);
		T->SetShadowOffset(FVector2D(1.f, 1.f));
		T->SetShadowColorAndOpacity(SSPalette::Ink950(0.6f));
		return T;
	}

	inline UBorder* Plate(UWidgetTree* Tree, const FLinearColor& Colour, const FMargin& Padding)
	{
		UBorder* B = Tree->ConstructWidget<UBorder>();
		B->SetBrushColor(Colour);
		B->SetPadding(Padding);
		return B;
	}

	inline UWidget* Rule(UWidgetTree* Tree, const FLinearColor& Colour, float Height, float Width = 0.f)
	{
		USizeBox* Size = Tree->ConstructWidget<USizeBox>();
		Size->SetHeightOverride(Height);
		if (Width > 0.f)
		{
			Size->SetWidthOverride(Width);
		}
		Size->AddChild(Plate(Tree, Colour, FMargin(0.f)));
		return Size;
	}

	inline UVerticalBoxSlot* AddV(UVerticalBox* Box, UWidget* Child, float Top = 0.f, EHorizontalAlignment H = HAlign_Fill)
	{
		UVerticalBoxSlot* Slot = Box->AddChildToVerticalBox(Child);
		Slot->SetHorizontalAlignment(H);
		Slot->SetPadding(FMargin(0.f, Top, 0.f, 0.f));
		return Slot;
	}

	inline UHorizontalBoxSlot* AddH(UHorizontalBox* Box, UWidget* Child, bool bFill = false, EVerticalAlignment V = VAlign_Center)
	{
		UHorizontalBoxSlot* Slot = Box->AddChildToHorizontalBox(Child);
		Slot->SetVerticalAlignment(V);
		Slot->SetSize(FSlateChildSize(bFill ? ESlateSizeRule::Fill : ESlateSizeRule::Automatic));
		return Slot;
	}

	/** Canvas slot pinned to an anchor, aligned to the same corner. */
	inline UCanvasPanelSlot* Pin(UCanvasPanel* Canvas, UWidget* Child, const FVector2D& Anchor, const FVector2D& Offset)
	{
		UCanvasPanelSlot* Slot = Canvas->AddChildToCanvas(Child);
		Slot->SetAnchors(FAnchors(Anchor.X, Anchor.Y));
		Slot->SetAlignment(Anchor);
		Slot->SetPosition(Offset);
		Slot->SetAutoSize(true);
		return Slot;
	}

	inline UCanvasPanelSlot* Fill(UCanvasPanel* Canvas, UWidget* Child)
	{
		UCanvasPanelSlot* Slot = Canvas->AddChildToCanvas(Child);
		Slot->SetAnchors(FAnchors(0.f, 0.f, 1.f, 1.f));
		Slot->SetOffsets(FMargin(0.f));
		return Slot;
	}

	/** 0..1 ease-out progress of an animation starting at Delay seconds and lasting Duration. */
	inline float Ease(float Elapsed, float Delay, float Duration)
	{
		return FMath::InterpEaseOut(0.f, 1.f, FMath::Clamp((Elapsed - Delay) / Duration, 0.f, 1.f), 3.f);
	}

	/** Fade and slide a widget in from the left (or up when Vertical), driven by Ease. */
	inline void Reveal(UWidget* Widget, float Alpha, float Distance = 24.f, bool bVertical = false)
	{
		if (Widget)
		{
			Widget->SetRenderOpacity(Alpha);
			Widget->SetRenderTranslation(bVertical ? FVector2D(0.f, (1.f - Alpha) * Distance) : FVector2D((1.f - Alpha) * -Distance, 0.f));
		}
	}

	/** Flat menu button: field plate, brass on hover, sand label. */
	inline UButton* MenuButton(UWidgetTree* Tree, const FText& Label, float Width = 420.f)
	{
		UButton* Button = Tree->ConstructWidget<UButton>();
		FButtonStyle Style = Button->GetStyle();
		auto Flat = [](const FLinearColor& C)
		{
			FSlateBrush Brush;
			Brush.DrawAs = ESlateBrushDrawType::Box;
			Brush.TintColor = FSlateColor(C);
			return Brush;
		};
		Style.SetNormal(Flat(SSPalette::Field800(0.92f)));
		Style.SetHovered(Flat(SSPalette::Brass500(0.95f)));
		Style.SetPressed(Flat(SSPalette::Brass300()));
		Style.SetNormalPadding(FMargin(18.f, 12.f));
		Style.SetPressedPadding(FMargin(18.f, 13.f, 18.f, 11.f));
		Button->SetStyle(Style);
		USizeBox* Size = Tree->ConstructWidget<USizeBox>();
		Size->SetWidthOverride(Width);
		UTextBlock* T = Text(Tree, 15, true, SSPalette::Sand100(), 120);
		T->SetText(Label);
		Size->AddChild(T);
		Button->AddChild(Size);
		return Button;
	}
}
